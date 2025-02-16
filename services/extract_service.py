"""Module that contains data extraction logic."""

from urllib.parse import parse_qs
from urllib.parse import urlparse

from playwright.async_api import Page, Locator

from logger.logger import logger


async def parse_page(
    browser_page: Page,
) -> tuple[dict[int, tuple[str, int, int, str, str, str, str, int, str]], bool]:
    """Parses the page and extracts data.
    Returns a dictionary of listings and a boolean if there are more pages.
    :param browser_page: Page
    :return: dict[str, tuple[str, str | None, str, float, float, int, str | None, str | None]], bool
    """

    logger.debug("Parsing page %s.", browser_page.url)

    # Reject cookies.
    # check if the cookie dialog is present.
    if (
        len(await browser_page.locator("#CybotCookiebotDialogBodyButtonDecline").all())
        > 0
    ):
        await browser_page.locator("#CybotCookiebotDialogBodyButtonDecline").click()

    # Wait for the page to load.
    await browser_page.wait_for_load_state("domcontentloaded")

    extracted_data = {}

    # pylint: disable=line-too-long
    results = await browser_page.locator(
        "//*[@id='results']/div[contains(@class, 'GO-Results-Row')]"
    ).all()

    # Loop through all the listings.
    for result in results:
        item_id, data = await parse_result(result)
        extracted_data[item_id] = data

    # Check if the page has next page buttons.
    has_buttons = (
        await browser_page.locator(
            """
    //*[@id='GO-naviprevnext']/li[contains(@class, 'GO-Rounded-R')]
    """
        ).count()
        != 0
    )

    # Check if next page buttons is disabled. If so, there are no more pages.
    more_pages = has_buttons and (
        await browser_page.locator(
            """
        //*[@id="GO-naviprevnext"]/li[contains(@class, 'GO-Rounded-R') and contains(@class, 'disabled')]
        """
        ).count()
        == 0
    )

    logger.debug("More pages: %s", more_pages)

    logger.info("Parsing page %s finished.", browser_page.url)

    return extracted_data, more_pages


# pylint: disable=(too-many-locals
async def parse_result(
    item: Locator,
) -> tuple[int, tuple[str, int, int, str, str, str, str, int, str]]:
    """Extracts data from the result."""

    logger.debug("Extracting result data...")

    # Check if image is present.
    image_locator = item.locator('xpath=div[contains(@class, "GO-Results-Photo")]/div/a/img')
    if await image_locator.count() == 0:
        image_url = await item.locator(
            'xpath=div[contains(@class, "GO-Results-Photo")]/div/a/img'
        ).first.get_attribute("src")

    title = await item.locator(
        'xpath=div[contains(@class, "GO-Results-Naziv ")]/span'
    ).inner_text()

    details = item.locator(
        'xpath=div[contains(@class, "GO-Results-Data")]/div/table/tbody'
    )

    rows = await details.locator("tr").all()

    year = None
    kilometers = None
    fuel = None
    transmission = None
    engine = None
    price = None

    for row in rows:
        cells = await row.locator("td").all()

        name = await cells[0].inner_text()
        value = await cells[1].inner_text()

        match name:
            case "1.registracija":
                year = int(value)
            case "Prevoženih":
                kilometers = int(value.split(" ")[0])
            case "Gorivo":
                fuel = value.split(" ")[0]
            case "Menjalnik":
                transmission = value.split(" ")[0]

            case "Motor":
                engine = value
            case _:
                logger.warning("Unknown table details name: %s", name)

    url = (
        await item.locator(
            'xpath=a[contains(@class, "stretched-link")]'
        ).first.get_attribute("href")
    )[2:]

    # fix relative url.
    url = f"https://www.avto.net{url}"

    # check whether the item contains sale css class.
    price_group = item.locator('xpath=div[contains(@class, "GO-Results-PriceLogo")]')

    # pylint: disable=line-too-long
    if (
        len(
            await price_group.locator(
                'xpath=div[contains(@class, "GO-Results-Price-Akcija")]'
            ).all()
        )
        > 0
    ):
        price = await price_group.locator("xpath=div[1]/div[2]/div[2]").inner_text()
    else:
        price = await price_group.locator("xpath=div[1]/div[1]/div[1]").inner_text()

    price = int(price.split(" ")[0].replace(".", ""))

    parsed_url = urlparse(url)

    item_id = int(parse_qs(parsed_url.query)["id"][0])

    logger.debug(
        """
    Title: %s,
    Item ID: %d,
    Year: %d,
    Kilometers: %s,
    Transmission: %s,
    Fuel: %s,
    Engine: %s,
    URL: %s,
    Price: %d,
    Image URL: %s,
    """,
        title,
        item_id,
        year,
        kilometers,
        transmission,
        fuel,
        engine,
        url,
        price,
        image_url,
    )

    logger.debug("Parsing result finished.")

    return item_id, (
        title,
        year,
        kilometers,
        transmission,
        fuel,
        engine,
        url,
        price,
        image_url,
    )
