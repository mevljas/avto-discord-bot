# pylint: disable=too-many-locals
"""
Module that contains discord bot logic.
"""

import logging

import discord
from discord.ext import tasks

from database.database_manager import DatabaseManager
from spider.spider import run_spider


class MyDiscordClient(discord.Client):
    """
    Avto.si Discord bot client.
    """

    def __init__(self, database_path):
        self.database_path = database_path
        super().__init__(intents=discord.Intents.default())

    async def setup_hook(self) -> None:
        # start the task to run in the background
        self.my_background_task.start()

    async def on_ready(self):
        """
        Called when the bot is ready.
        :return:
        """
        logging.debug("""Logged in as %s (ID: %s)""", self.user, self.user.id)
        logging.debug("------")

    @tasks.loop(hours=24)  # task runs every 1 hour
    async def my_background_task(self):
        """
        Background task that runs every day.
        :return:
        """

        logging.info("Scan started.")

        # Setup database manager.
        database_manager = DatabaseManager(
            url="sqlite+aiosqlite:///" + self.database_path
        )

        # Run the spider.
        channel_listings, error = await run_spider(database_manager=database_manager)

        for channel_id, listings in channel_listings.items():
            logging.debug("Sending listings to channel %s.", channel_id)

            channel = self.get_channel(int(channel_id))  # channel ID goes here
            # await channel.send("Hello, world!")

            logging.debug("Found %s new listings.", len(listings))

            await channel.send(f"Found {len(listings)} new listings.")

            for listing in listings:
                # pylint: disable=line-too-long
                (
                    title,
                    year,
                    kilometers,
                    transmission,
                    fuel,
                    engine,
                    url,
                    prices,
                    image_url,
                ) = listing

                logging.debug("Listing: %s", listing)

                embed = discord.Embed(
                    title=title,
                    url=url,
                    color=discord.Color.blue(),
                )
                if image_url:
                    embed.set_image(url=image_url)
                embed.add_field(
                    name="**Letnik**",
                    value=year,
                    inline=True,
                )
                embed.add_field(
                    name="**Kilometri**",
                    value=f"{kilometers} km",
                    inline=True,
                )
                embed.add_field(
                    name="**Menjalnik**",
                    value=transmission,
                    inline=True,
                )
                embed.add_field(
                    name="**Gorivo**",
                    value=fuel,
                    inline=True,
                )
                embed.add_field(
                    name="**Motor**",
                    value=engine,
                    inline=True,
                )
                embed.add_field(
                    name="**Cena**",
                    value=f"{prices[0]:.2f} €",
                    inline=True,
                )

                if len(prices) > 1:
                    embed.add_field(
                        name="**Prejšnje cene**",
                        value=", ".join(f"{price:.2f} €" for price in prices[1:]),
                        inline=False,
                    )

                await channel.send(embed=embed)

            if error:
                await channel.send("An error occurred while scanning the listings.")

        logging.info("Scan finished.")

    @my_background_task.before_loop
    async def before_my_task(self):
        """
        Wait until the bot is ready.
        :return:
        """
        await self.wait_until_ready()  # wait until the bot logs in
