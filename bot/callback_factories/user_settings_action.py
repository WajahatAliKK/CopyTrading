from aiogram.filters.callback_data import CallbackData


from typing import Optional, Union
# start_action = CallbackData("start", "type", "value")
class UserSettingsAction(CallbackData, prefix="user_settings"):
    column: str
    value: Optional[Union[int, str]]
    network: Optional[Union[int, str]]