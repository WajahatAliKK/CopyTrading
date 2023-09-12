# from aiogram import executor
from bot.app import dp, bot
import asyncio


async def start_bot():
    while True:
        try:
            # print(dp.resolve_used_update_types())
            
            await bot.delete_webhook(drop_pending_updates=True)
            await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await asyncio.sleep(5)  # Add a short sleep before restarting the bot


async def main():
    try:
        await start_bot()
    except KeyboardInterrupt:
        print("Bot is stopping...")


async def main_wrapper():
    tasks = [
        asyncio.create_task(main())
    ]

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    try:
        asyncio.run(main_wrapper())
    except (KeyboardInterrupt, SystemExit):
        print("Bot stopped!")