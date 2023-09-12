from aiogram.filters.callback_data import CallbackData


from typing import Optional, Union
# start_action = CallbackData("start", "type", "value")
class Back(CallbackData, prefix="back"):
    type: str
    value: Optional[Union[int, str]]