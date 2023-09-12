# callback_factories/wallet.py
from aiogram.filters.callback_data import CallbackData
from typing import Optional, Union



# wallet_action = CallbackData("wallet", "type", "value")

class WalletAction(CallbackData, prefix="wallet"):
    type: str
    value: Optional[Union[int, str]]
    action: Optional[Union[int, str]]
    wallet_id: Optional[int]
