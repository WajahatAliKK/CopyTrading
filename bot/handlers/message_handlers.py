from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton

from db_utils import get_user_data, update_user
from utils import is_token_address, get_token_info

from bot.keyboards.menu_keyboard import token_keyboard


@dp.message_handler(content_types=types.ContentTypes.TEXT)
async def message_handler(message: types.Message, state: FSMContext, user_data: dict):
    text = message.text

    if is_token_address(text):
        token_info = get_token_info(text)
        response_text = f"Token Information:\n\nName: {token_info['name']}\nSymbol: {token_info['symbol']}\nDecimals: {token_info['decimals']}"

        if user_data['paid'] or user_data['holds_token']:
        
            await message.answer(response_text, reply_markup=token_keyboard, parse_mode=ParseMode.MARKDOWN)
        else:
            await message.answer(response_text, parse_mode=ParseMode.MARKDOWN)
    else:
        # Handle other text messages here
        pass
