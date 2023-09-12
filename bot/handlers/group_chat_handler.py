from aiogram import types
from bot.utils.config import GROUP_CHAT_ID
from database.user_functions import update_user_group_status, get_user
from bot.handlers.routers import group_handler
from aiogram.types import ContentType

import logging
from bot.db_client import db


@group_handler.message(lambda message: message.content_type == ContentType.NEW_CHAT_MEMBERS)
async def new_member_handler(message: types.Message):
    # logging.info("New member handler triggered")
    if message.chat.id == GROUP_CHAT_ID:
        for member in message.new_chat_members:
            if not member.is_bot:
                user_data = await get_user(member, db)
                if user_data:
                    resp = await update_user_group_status(user_data.chat_id, True, db)
                    


@group_handler.message(lambda message: message.content_type == ContentType.LEFT_CHAT_MEMBER)
async def member_left_handler(message: types.Message):
    # logging.info("leaving member handler triggered")
    if message.chat.id == GROUP_CHAT_ID:
        user_data = await get_user(message.left_chat_member, db)

        if user_data:
            resp = await update_user_group_status(user_data.chat_id, False, db)
            

