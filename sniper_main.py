
import asyncio
from bot.snipers.sniper_initializer import initialize_snipers


async def main_wrapper():
    tasks = [
        asyncio.create_task(initialize_snipers())
    ]

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    try:
        asyncio.run(main_wrapper())
    except (KeyboardInterrupt, SystemExit):
        print("Bot stopped!")