from aiogram.filters.callback_data import CallbackData


from typing import Optional, Union
# start_action = CallbackData("start", "type", "value")
class TradeAction(CallbackData, prefix="trade"):
    value: str
    trade_id: int
    
