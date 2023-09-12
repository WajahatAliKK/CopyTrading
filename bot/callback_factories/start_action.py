from aiogram.filters.callback_data import CallbackData


from typing import Optional, Union
# start_action = CallbackData("start", "type", "value")
class StartAction(CallbackData, prefix="start"):
    type: str
    value: Optional[Union[int, str]]
    action: Optional[Union[int, str]]