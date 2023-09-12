# handlers/start.py
from aiogram import types
from aiogram.fsm.context import FSMContext

from bot.keyboards.fresh_user_kb import new_user_keyboard
from bot.keyboards.paid_user_kb import paid_user_keyboard, start_menu_keyboard
from bot.keyboards.menu_keyboard import wallet_manager_keyboard

from bot.db_client import db
from bot.kb_texts.all_messages import no_wallet
from database.user_functions import get_user, get_user_by_chat_id
from database.trade_functions import get_trades_by_user_id
from database.wallet_functions import user_has_wallet
from aiogram.filters import Command, StateFilter
from bot.utils.config import HOLDING_TOKEN_NAME, HOLDING_QUANTITY, ETH_FEE, GROUP_TITLE
from bot.callback_factories.back import Back
from bot.handlers.routers import start_menu
from bot.kb_texts.all_messages import home_message
from aiogram import F

@start_menu.callback_query(Back.filter(F.type=="main_menu"), StateFilter('*'))
async def start_func(query: types.CallbackQuery, callback_data: dict, state):
    await state.set_state(None)
    user_data = await get_user_by_chat_id(query.from_user.id, db)
    network = "Ethereum"
    has_wallet = True if [x for x in user_data.wallets if x.network.lower()==network.lower()] else False
    if not has_wallet:
        await query.message.edit_text(text=no_wallet, reply_markup=wallet_manager_keyboard(False),parse_mode='MarkDown')
        return
    
    trades = await get_trades_by_user_id(user_data.id,db)
    if trades:
        kb = paid_user_keyboard(user_data,has_trades=True)
        active_trades_count = len(trades)
        text = home_message
    else:
        kb = paid_user_keyboard(user_data)
        text = home_message
    
    await query.message.edit_text(text, reply_markup=kb,parse_mode='MarkDown')
    return
    
    # await query.message.edit_text(welcome_message, reply_markup=kb)


@start_menu.message(Command(commands=["start", "sniper"]), StateFilter("*"))
async def start_command(message: types.Message, state:FSMContext):
    await state.clear()
    await state.set_state(None)
    user_data = await get_user_by_chat_id(message.from_user.id, db)
    text = home_message
    if user_data.username:
        text += f"Hey {user_data.username}\n\n"
    await message.answer(text=text, reply_markup=start_menu_keyboard(),parse_mode='MarkDown')