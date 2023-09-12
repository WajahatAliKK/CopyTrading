import logging
import asyncio
from aiogram import Bot, Dispatcher, types
# from aiogram.contrib.middlewares.logging import LoggingMiddleware
import logging




from bot.handlers.start import start_command
from bot.middlewares.user_check import UserCheckMiddleware
from bot.middlewares.database_middleware import DatabaseMiddleware
from bot.middlewares.debug_middleware import DebugMiddleware

from concurrent.futures import ThreadPoolExecutor
# from sniper_initializer import initialize_snipers

from bot.utils.config import *
from bot.db_client import db

from bot.handlers.routers import wallet_menu, start_menu, payment_menu, group_handler, user_settings_menu, ca_menu

# def run_snipers(web3_eth_instance, web3_bsc_instance, web3_arb_instance):
#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)
#     loop.run_until_complete(initialize_snipers(web3_eth_instance, web3_bsc_instance, web3_arb_instance))
#     loop.close()

from bot.utils.config import GROUP_CHAT_ID

def get_logger_f():

    logger = logging.getLogger(__name__)
    logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        )
    return logger
logger = get_logger_f()
logger.info("Starting bot")

def get_bot():
    return Bot(token=BOT_TOKEN, parse_mode='HTML')

bot = get_bot()
dp = Dispatcher()



# dp.middleware.setup(LoggingMiddleware())
dp.message.middleware(UserCheckMiddleware())
dp.callback_query.middleware(UserCheckMiddleware())

dp.message.middleware(DatabaseMiddleware())
dp.callback_query.middleware(DatabaseMiddleware())




dp.include_router(wallet_menu)
dp.include_router(start_menu)
dp.include_router(payment_menu)
dp.include_router(group_handler)
dp.include_router(user_settings_menu)
dp.include_router(ca_menu)




# async def on_startup(dp):
#     await tbot.send_message(chat_id=ADMIN_CHAT_ID, text="Bot has been started")
    

# async def on_shutdown(dp):
#     await tbot.send_message(chat_id=ADMIN_CHAT_ID, text="Bot has been stopped")

#     await tbot.close()


# if __name__ == "__main__":
#     from aiogram import executor
#     executor.start_polling(dp, on_startup=on_startup, on_shutdown=on_shutdown)
