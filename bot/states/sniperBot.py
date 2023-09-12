from aiogram.fsm.state import StatesGroup, State



class SniperBotState(StatesGroup):
    menu = State()  # Main menu state
    subscription_menu = State()  # Subscription management state
    user_setting_menu = State()  # User settings management state
    token_info_menu = State()  # Token information display and action state
    start = State()
    user_setting_menu = State()


class WalletState(StatesGroup):
    choose_network = State()
    generate_wallet = State()
    remove_wallet = State()
    enter_wallet_address = State()
    connect_wallet = State()
    ask_for_name = State()


class UserSettingsState(StatesGroup):
    sniper_amount = State()
    set_tp = State()
    set_sl = State()
    set_min_liq = State()
    set_gas_delta = State()
    set_slippage = State()
    set_sell_slippage = State()
    set_blocks_wait = State()


class PaymentStates(StatesGroup):
    swap = State()

class CAStates(StatesGroup):
    buyX = State()
    sellX = State()
