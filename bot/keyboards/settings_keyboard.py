from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.callback_factories.user_settings_action import UserSettingsAction
from bot.callback_factories.back import Back
from aiogram.utils.keyboard import InlineKeyboardBuilder 
from aiogram.filters.callback_data import CallbackData
from bot.callback_factories.start_action import StartAction


def user_settings_keyboard(network):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            
            [InlineKeyboardButton(text="🎯 Sniper Configurations", callback_data="none")],

            [InlineKeyboardButton(text="🎩 Snipe Amount", callback_data=UserSettingsAction(column="amount_per_snipe", network=network).pack())],
            
            [
                InlineKeyboardButton(text="⚡ Gas Budget", callback_data=UserSettingsAction(column="max_gas_price", network=network).pack()),
                InlineKeyboardButton(text="🔮 Repeat Purchase", callback_data=UserSettingsAction(column="duplicate_buy", network=network).pack())
            ],

            [
                InlineKeyboardButton(text="🌊 Min. Liquidity", callback_data=UserSettingsAction(column="min_liquidity", network=network).pack()),
                InlineKeyboardButton(text="⏳ Wait Blocks", callback_data=UserSettingsAction(column="blocks_to_wait", network=network).pack()),
            ],

            [
                InlineKeyboardButton(text="🌀 Trade Slippage", callback_data=UserSettingsAction(column="set_slippage_settings", network=network).pack())
            ],

            [
                InlineKeyboardButton(text="🧐 Scam Spotter", callback_data=UserSettingsAction(column="honeypot_settings", network=network).pack())
            ],

            [
                InlineKeyboardButton(text="© Start Copy Trading", callback_data=UserSettingsAction(column="startcopytradebtn" , network=network).pack())
            ],
            [
                InlineKeyboardButton(text="↕ Update Copy Trade Percentage" , callback_data=UserSettingsAction(column="updatecopytradepercentage" , network=network).pack())
            ],
            [InlineKeyboardButton(text="🏡 Home Menu", callback_data=Back(type="main_menu").pack())],
        ]
    )
    return kb

class btnfortradecopy(CallbackData , prefix = 'call'):
    strt : str
    endno : int

def addaddresskeyboard(wallet_len):
    add_address = InlineKeyboardBuilder()
    if wallet_len <= 1:
        add_address.button(text="Add copy Address" , callback_data=btnfortradecopy(strt="addaddress" , endno=1))
        add_address.button(text="Delete copy Address" , callback_data=btnfortradecopy(strt="deleteaddress" , endno=1))
        add_address.button(text="🔙 Back Menu", callback_data=StartAction(type="user_settings").pack())
        add_address.adjust(2,1)
        return add_address
    else:
        add_address.button(text="Delete copy Address" , callback_data=btnfortradecopy(strt="deleteaddress" , endno=1))
        add_address.button(text="🔙 Back Menu", callback_data=StartAction(type="user_settings").pack())
        add_address.adjust(2,1)
        return add_address


def backbutton_to_setting():
    backto_setting = InlineKeyboardBuilder()

    backto_setting.button(text="⚙️ Back TO Settings" , callback_data=StartAction(type="user_settings").pack())

    return backto_setting
