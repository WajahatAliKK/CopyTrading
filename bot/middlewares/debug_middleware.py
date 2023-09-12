from aiogram import BaseMiddleware
import logging

class DebugMiddleware(BaseMiddleware):
    async def on_pre_process_update(self, update, data):
        logging.info(f"Received update: {update}")

