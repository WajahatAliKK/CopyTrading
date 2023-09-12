from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.callback_factories.user_settings_action import UserSettingsAction
from bot.callback_factories.back import Back


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

            [InlineKeyboardButton(text="🏡 Home Menu", callback_data=Back(type="main_menu").pack())],
        ]
    )
    return kb


