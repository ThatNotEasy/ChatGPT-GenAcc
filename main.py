"""
ChatGPT Account Creator - Main Entry Point
This script automates the creation of ChatGPT accounts using temporary browser data.
Converted from Node.js Playwright to Python Playwright.
"""
import asyncio
import sys

from modules.config import Config
from modules.logging import Logger
from modules.chatgpt import ChatGPTAccountCreator


async def main():
    """Main entry point for the application"""
    print("ChatGPT Account Creator")
    print("=" * 60)

    # Initialize components
    config = Config()
    logger = Logger()
    creator = ChatGPTAccountCreator(config, logger)

    # Validate password configuration
    is_valid, error_msg = config.validate_password()
    if not is_valid:
        logger.log(error_msg, "ERROR")
        print("\nPlease update your config.json file with a valid password (at least 12 characters).")
        return

    print("Configuration loaded")
    print()

    try:
        answer = input("\nHow many accounts do you want to create? ")

        num_accounts = int(answer)
        if num_accounts <= 0:
            print("Please enter a positive number!")
            return

        print(f"\nStarting creation of {num_accounts} account(s)...")
        print("   Processing one account at a time (sequential mode)\n")

        await creator.create_accounts(num_accounts)

    except KeyboardInterrupt:
        print("\n\nScript interrupted by user (Ctrl+C)")
        print("Progress saved to accounts.txt")
    except ValueError:
        print("\nPlease enter a valid number!")
    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nScript interrupted by user (Ctrl+C)")
        print("Progress saved to accounts.txt")
