from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types.base import TelegramObject
from bot.db_client import db
import logging

class DatabaseMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # logging.info(f"Received update: {update}")
        data["db"] = db
        return await handler(event, data)

   