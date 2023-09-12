from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.callback_factories.start_action import StartAction
from bot.utils.config import HOLDING_TOKEN_NAME, HOLDING_QUANTITY, ETH_FEE, GROUP_URL


def new_user_keyboard(user_data, has_wallet):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            
            [
             InlineKeyboardButton(text="🔐 Manage Wallets", callback_data=StartAction(type="wallets", value=user_data.id).pack())
            ],
            [
                InlineKeyboardButton(text="🔗 Group Link", url=GROUP_URL)
            ] if not user_data.joined_channel else [],
            [
                InlineKeyboardButton(text=f"💰 Pay (300 USDT)", callback_data=StartAction(type="payment", value="payment").pack()),
                InlineKeyboardButton(text=f"🔥 Burn {HOLDING_QUANTITY} {HOLDING_TOKEN_NAME}", callback_data=StartAction(type="burn", value="burn").pack())] if not (user_data.paid or user_data.holds_token) and (has_wallet) else [],
                [InlineKeyboardButton(text=f"🛍️ Buy {HOLDING_QUANTITY} {HOLDING_TOKEN_NAME} Tokens", callback_data=StartAction(type="hold_tokens", value=user_data.id).pack())
                 
                
            ] if not (user_data.paid or user_data.holds_token) and (has_wallet) else [],
            [InlineKeyboardButton(text="🏪 Contact Support", url="https://t.me/+FAxovzDcgiljODEx")]
        ]
    )
    return kb



