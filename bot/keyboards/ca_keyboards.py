from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.callback_factories.ca_action import BuyAction, SellAction

def buy_keyboard(network, coin_id, pool_address):
    
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔍 Monitor", callback_data=BuyAction(amount="track", network=network, coin=coin_id).pack()),
                InlineKeyboardButton(text="🔄 Toggle Buy/Sell", callback_data=BuyAction(amount="switch", network=network, coin=coin_id).pack()),
                InlineKeyboardButton(text="📊 View Chart", url=f"https://www.dexscreener.com/{network}/{pool_address}")
            ],
            [
                InlineKeyboardButton(text="Get 0.01 ETH", callback_data=BuyAction(amount="0.01", network=network, coin=coin_id).pack()),
                InlineKeyboardButton(text="Get 0.05 ETH", callback_data=BuyAction(amount="0.05", network=network, coin=coin_id).pack()),
                InlineKeyboardButton(text="Get 0.1 ETH", callback_data=BuyAction(amount="0.1", network=network, coin=coin_id).pack())
            ],
            [
                InlineKeyboardButton(text="Get 0.2 ETH", callback_data=BuyAction(amount="0.2", network=network, coin=coin_id).pack()),
                InlineKeyboardButton(text="Get 0.5 ETH", callback_data=BuyAction(amount="0.5", network=network, coin=coin_id).pack())
            ],
            [
                InlineKeyboardButton(text="Get 1 ETH", callback_data=BuyAction(amount="1", network=network, coin=coin_id).pack()),
                InlineKeyboardButton(text="Specify Amount in ETH", callback_data=BuyAction(amount="X", network=network, coin=coin_id).pack()),
                InlineKeyboardButton(text="Go All-In!", callback_data=BuyAction(amount="max", network=network, coin=coin_id).pack())
            ],
        ]
    )
    return kb



def sell_keyboard(network, coin_id, pool_address):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔍 Monitor", callback_data=BuyAction(amount="track", network=network,coin=coin_id).pack()),
                InlineKeyboardButton(text="🔄 Toggle Buy/Sell", callback_data=SellAction(amount="switch", network=network,coin=coin_id).pack()),
                InlineKeyboardButton(text="📊 View Chart", url=f"https://www.dexscreener.com/{network}/{pool_address}")
            ],
            [
                InlineKeyboardButton(text="🔄 Specify Sell Percentage", callback_data=SellAction(amount="sell_x", network=network,coin=coin_id).pack())
            ],
            [
                InlineKeyboardButton(text="🔄 Liquidate 25% Holdings", callback_data=SellAction(amount="25", network=network,coin=coin_id).pack()),
                InlineKeyboardButton(text="🔄 Liquidate 50% Holdings", callback_data=SellAction(amount="50", network=network,coin=coin_id).pack())
            ],
            [
                InlineKeyboardButton(text="🔄 Liquidate 75% Holdings", callback_data=SellAction(amount="75", network=network,coin=coin_id).pack()),
                InlineKeyboardButton(text="🔄 Liquidate All Holdings", callback_data=SellAction(amount="100", network=network,coin=coin_id).pack())
            ],
        ]
        
    )
    return kb

