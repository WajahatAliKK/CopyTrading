from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.callback_factories.start_action import StartAction
from bot.callback_factories.wallet import WalletAction
from bot.callback_factories.back import Back

# def paid_user_keyboard(user, has_trades=False):
#     kb = InlineKeyboardMarkup(inline_keyboard=[
#                                                 [InlineKeyboardButton(text="=> tobinU Sniper - Elite Auto Trader <=", callback_data="none")],
#                                                 [InlineKeyboardButton(text=f"{'🟢 Bot is Active' if user.is_active else '🔴 Bot is Disabled' }", callback_data=StartAction(type="bot_active").pack())],
#                                                 [InlineKeyboardButton(text="🔐 Manage Wallets", callback_data=StartAction(type="wallets").pack()),
#                                                InlineKeyboardButton(text="🔧 Bot Settings", callback_data=StartAction(type="bot_settings").pack())],
#                                             #    [InlineKeyboardButton(text="✅ Approve Balance", callback_data=StartAction(type="approve_balance").pack())],
#                                                [InlineKeyboardButton(text="🤝 Manage Trades", callback_data=StartAction(type="manage_trades").pack())] if has_trades else [],
#                                                [InlineKeyboardButton(text="🏪 Contact Support", url="https://t.me/tobinusnipersupport")]

#                                                                     ])
     
#     return kb

def start_menu_keyboard():
    kb = InlineKeyboardMarkup(inline_keyboard=[
                                                [InlineKeyboardButton(text="🏃🏻 Let's Go!! 🏃🏻", callback_data=Back(type="main_menu").pack())]
                                            ])

    return kb



def paid_user_keyboard(user, has_trades=False):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{'✅ Bot Up ✅' if user.is_active else '❌ Bot Down ❌'}", callback_data=StartAction(type="bot_active").pack())],
        [InlineKeyboardButton(text="🧐 Oversee Trades", callback_data=StartAction(type="manage_trades").pack())] if has_trades else [],
        [InlineKeyboardButton(text="⚙️ Preferences", callback_data=StartAction(type="user_settings").pack()),
         InlineKeyboardButton(text="🔒 Wallet Manager", callback_data=StartAction(type="wallets").pack())],
        [InlineKeyboardButton(text="💰 Get Withdraw", callback_data=WalletAction(type="withdraw", action="wm_main").pack())],
    ])

    return kb




def group_join_keyboard():
    kb = InlineKeyboardMarkup(inline_keyboard=[
                                                
                                                [InlineKeyboardButton(text="🤝 Join Group", url="https://t.me/+LWXFvNnuPqBhZDcx")],
                                                [InlineKeyboardButton(text="🏪 Contact Support", url="https://t.me/tobinusnipersupport")]
                                                ])
     
    return kb
