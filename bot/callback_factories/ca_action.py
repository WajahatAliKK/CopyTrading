from aiogram.filters.callback_data import CallbackData
from database.models import Coin

from typing import Optional, Union
# start_action = CallbackData("start", "type", "value")




class BuyAction(CallbackData, prefix="buy"):
    amount: str
    network: str
    coin: int


class SellAction(CallbackData, prefix="sell"):
    amount: str
    network: str
    coin: int