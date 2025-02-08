"""Module that contains main application logic."""

import asyncio
import os

from dotenv import load_dotenv

from database.database_manager import DatabaseManager
from logger.logger import logger
from services.discord_service import MyDiscordClient


def load_env() -> tuple[str, str]:
    """
    Loads ENV variables.
    :return: discord_token, database_path
    """
    load_dotenv()
    discord_token = os.getenv("DISCORD_TOKEN")
    database_path = os.getenv("DB_PATH")
    return discord_token, database_path


async def setup_db(database_path: str):
    """
    Sets up the database.
    :param database_path: str
    :return:
    """
    logger.info("DB setup started.")

    # Delete existing database if it exists.
    if os.path.exists(database_path):
        os.remove(database_path)

    # Setup database manager.
    database_manager = DatabaseManager(url="sqlite+aiosqlite:///" + database_path)

    # Create database tables.
    await database_manager.create_models()

    # Clean database manager.
    await database_manager.cleanup()
    logger.info("DB setup finished.")


def main():
    """
    Main function.
    :return:
    """
    logger.info("Application started.")

    # Load env variables.
    discord_token, database_path = load_env()

    # Setup database if it does not exist.
    if not os.path.exists(database_path):
        logger.debug("Database does not exist. Setting up database.")
        asyncio.run(setup_db(database_path))

    else:
        logger.debug("Database already exists.")

    discord_client = MyDiscordClient(database_path=database_path)
    discord_client.run(token=discord_token, log_handler=None)

    logger.info("Application finished.")


if __name__ == "__main__":
    main()
