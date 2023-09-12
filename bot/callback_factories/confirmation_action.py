from aiogram.filters.callback_data import CallbackData

class ConfirmAction(CallbackData, prefix="confirm"):
    type: str
    value: str
    action: str
