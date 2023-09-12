from aiogram.types import CallbackQuery
from aiogram.filters.callback_data import CallbackData

# For handling user subscriptions
class SubscriptionAction(CallbackData):
    type: str
    value: str

# For handling user settings
class UserSettingAction(CallbackData):
    type: str
    value: str

# For handling token information display and actions
class TokenAction(CallbackData):
    type: str
    value: str

