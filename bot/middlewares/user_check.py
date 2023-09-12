from aiogram import BaseMiddleware
from aiogram import types
from bot.db_client import db
from database.user_functions import add_user, update_user, get_user

class UserCheckMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        if isinstance(event, types.Message) or isinstance(event, types.CallbackQuery):
            
            user_data = event.from_user
            user = await get_user(user_data, db)
            
            if user:
                await update_user(user_data, db)
            else:
                await add_user(event.from_user, db)

            data["user_data"] = user

        
        return await handler(event, data)
