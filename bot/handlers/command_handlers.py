from aiogram import types
from aiogram.dispatcher.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.keyboards.menu_keyboard import main_menu_keyboard

from main import dp


@dp.message_handler(Command("start"))
async def start_command_handler(message: types.Message, data: dict):
    user_data = data["user_data"]
    has_joined_channel = user_data["joined_channel"]
    has_paid = user_data["paid"]
    holds_required_token = user_data["holds_token"]

    if not has_joined_channel or not (has_paid or holds_required_token):
        keyboard = InlineKeyboardMarkup(row_width=1)

        if not has_joined_channel:
            keyboard.add(InlineKeyboardButton("Join Channel", url="https://t.me/yourchannel"))
        if not has_paid:
            keyboard.add(InlineKeyboardButton("Payment Menu", callback_data="payment_menu"))
        if not holds_required_token:
            keyboard.add(InlineKeyboardButton("Token Info", callback_data="token_info"))

        await message.reply("Please join our channel, make a payment, or hold the required token to proceed.", reply_markup=keyboard)
    else:
        # Continue with the start command functionality for users who meet the requirements
        await message.reply("Welcome to the bot!",reply_markup=main_menu_keyboard)