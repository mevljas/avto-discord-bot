# pylint: disable=too-many-locals
"""Module that contains main spider logic."""
from collections import defaultdict

from playwright.async_api import async_playwright

from database.database_manager import DatabaseManager
from logger.logger import logger
from services.extract_service import parse_page


async def run_spider(database_manager: DatabaseManager):
    """
    Setups the playwright library and starts the crawler.
    """
    logger.info("Spider started.")

    # Dictionary to store the listings. Key is the channel name.
    discord_listings = defaultdict(list)

    async with async_playwright() as playwright:
        # Connect to the browser.
        browser = await playwright.chromium.launch(headless=False)

        # Read page urls from a config file.
        config = await read_config()

        saved_results = await database_manager.get_listings()

        # For each url, send the results to a different channel.
        for channel, page_url in config:
            logger.info("Processing channel %s with URL %s", channel, page_url)

            discord_listings[channel] = []

            # create a new page inside context.
            browser_page = await browser.new_page(
                # pylint: disable=line-too-long
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
            )

            # Prevent loading some resources for better performance.
            # await browser_page.route("**/*", block_aggressively)

            await browser_page.goto(page_url)

            # await browser_page.pause()

            more_pages = True

            results = {}

            error = False

            await browser_page.goto(page_url)

            while more_pages:

                try:
                    results_tmp, more_pages = await parse_page(
                        browser_page=browser_page
                    )
                    results.update(results_tmp)
                except Exception as e:  # pylint: disable=broad-except
                    logger.error("Error parsing page: %s", e)
                    error = True

                if more_pages:
                    # pylint: disable=line-too-long
                    await browser_page.click(
                        "//*[@id='GO-naviprevnext']/li[contains(@class, 'GO-Rounded-R')]"
                    )

            for avto_id, new_data in results.items():
                logger.debug("Listing ID: %s", avto_id)

                if avto_id in saved_results:
                    logger.debug("Listing already saved.")

                    (
                        _,
                        _,
                        _,
                        _,
                        _,
                        _,
                        _,
                        new_price,
                        _,
                    ) = new_data

                    listing_id, old_prices = saved_results[avto_id]

                    if old_prices[-1] != new_price:
                        logger.info("New saved_price detected for %s.", avto_id)
                        await database_manager.add_new_price(
                            listing_id=listing_id,
                            current_price=new_price,
                        )

                        # Merge old and new prices.
                        old_prices.append(new_price)
                        new_data = new_data[:7] + (old_prices,) + new_data[8:]

                        discord_listings[channel].append(new_data)

                    else:
                        logger.debug("No new saved_price detected.")

                    continue

                # We found a new listing.
                logger.info("New listing found %s.", avto_id)

                await database_manager.save_listing(avto_id, new_data)

                # Convert price to a list of prices
                new_data = new_data[:7] + ([new_data[7]],) + new_data[8:]
                discord_listings[channel].append(new_data)
            await browser_page.close()

    await browser.close()
    logger.info("Spider finished.")

    return discord_listings, error


async def read_config():
    """
    Read the config file.
    Each line in the file contains a channel name and a URL.
    """
    with open("config.txt", encoding="utf-8") as file:
        return [line.strip().split() for line in file.readlines()]
