from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.callback_factories.wallet import WalletAction
from bot.callback_factories.confirmation_action import ConfirmAction
from bot.callback_factories.start_action import StartAction
from bot.callback_factories.user_settings_action import UserSettingsAction
from bot.callback_factories.trades_manage import TradeAction
from bot.callback_factories.back import Back
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from database.models import ActiveTrades

def main_menu_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("Wallet Manager", callback_data="wallet_manager"),
            InlineKeyboardButton("Settings", callback_data="settings")
        ],
        [
            InlineKeyboardButton("Subscription", callback_data="subscription"),
            InlineKeyboardButton("Token Stats", callback_data="token_stats")
        ],
        [
            InlineKeyboardButton("Track Contract", callback_data="track_contract")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def wallet_manager_keyboard(has_wallet):
    
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
                            [
                                InlineKeyboardButton(text="🌱 Generate Fresh Wallet", callback_data=WalletAction(type="generate", action="wm_main").pack()),
                                InlineKeyboardButton(text="🔗 Link Your Wallet", callback_data=WalletAction(type="connect", action="wm_main").pack())
                            ] if not has_wallet else [],
                            [
                                InlineKeyboardButton(text="🗑 Disconnect Wallet", callback_data=WalletAction(type="delete", action="wm_main").pack())
                            ] if has_wallet else [],
                            
                            [InlineKeyboardButton(text="⬅️Go Back", callback_data=Back(type="main_menu").pack())]
    ])
    return kb


def back_to_main_kb():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️Go Back", callback_data=Back(type="main_menu").pack())]
    ])
    return kb

def confirmation_keyboard(action):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ For sure!!", callback_data=ConfirmAction(type="confirm_action", value="confirm",action=action).pack()),
            InlineKeyboardButton(text="❌ Ah! Never mind", callback_data=ConfirmAction(type="confirm_action", value="cancel",action=action).pack())
        ],
        [InlineKeyboardButton(text="⬅️Go Back", callback_data=Back(type="main_menu").pack())]
    ])
    return kb


def delete_wallet_keyboard(wallets):
    kb = InlineKeyboardMarkup(
        inline_keyboard= [
            [InlineKeyboardButton(text="🗑 Delete the Wallet!", callback_data=WalletAction(type="select_wallet", value=x.name, action=x.network, wallet_id=x.id).pack()) for x in wallets],
            [InlineKeyboardButton(text="⬅️Go Back", callback_data=Back(type="wallet_manager").pack())]
        ]
    )
    # for wallet_name in wallets:
    #     kb.add(InlineKeyboardButton(text=wallet_name, callback_data=WalletAction(type="select_wallet", value=wallet_name).pack()))
    # kb.add(InlineKeyboardButton(text="⬅️Go Back", callback_data=Back(type="wallet_manager").pack()))
    return kb

def manage_trade_keyboard(current_coin:ActiveTrades, prev_id: int, next_id: int, pair_address) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Next Trade ➡️", callback_data=TradeAction(value='next_coin',trade_id=next_id).pack()),
                InlineKeyboardButton(text="🚫 Remove Trade", callback_data=TradeAction(value='delete',trade_id=current_coin.id).pack())],
            [InlineKeyboardButton(text="📉 Analyze Chart", url=f"http://www.dexscreener.com/{current_coin.network}/{pair_address}")],
            [
                InlineKeyboardButton(text="💸 Let's Sell!!", callback_data=TradeAction(value='sell_now',trade_id=current_coin.id).pack()),
                InlineKeyboardButton(text="💥 Liquidate Everything", callback_data=TradeAction(value='sell_all',trade_id=current_coin.id).pack())
            ],
            [InlineKeyboardButton(text="⬅️Go Back", callback_data=Back(type="main_menu").pack())]
        ]
        
    )

    return kb




def ask_for_network(action: str):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
                
                [InlineKeyboardButton(text="🔗Ethereum", callback_data=StartAction(type="choose_network", value="ethereum", action=action).pack()),
                InlineKeyboardButton(text="🔗BSC", callback_data=StartAction(type="choose_network", value="bsc", action=action).pack()),
                InlineKeyboardButton(text="🔗Arbitrum", callback_data=StartAction(type="choose_network", value="arbitrum", action=action).pack()),
                InlineKeyboardButton(text="🔗Base", callback_data=StartAction(type="choose_network", value="base", action=action).pack())],
                [InlineKeyboardButton(text="🔙 Go Back", callback_data=StartAction(type="main_menu").pack())],
            
        ]
    )
    return keyboard
