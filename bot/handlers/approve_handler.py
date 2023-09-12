from aiogram import types
from aiogram.fsm.context import FSMContext
from bot.keyboards.paid_user_kb import paid_user_keyboard
from aiogram.filters.callback_data import CallbackData
from bot.utils.wallet_methods import eth_uni_m, eth_uni_mv3, arb_uni_m, eth_wm
from bot.db_client import db

from database.user_functions import get_user, get_user_by_chat_id
from database.wallet_functions import user_has_wallet
from aiogram.filters import Command, StateFilter
from bot.utils.config import HOLDING_TOKEN_NAME, HOLDING_QUANTITY, ETH_FEE, GROUP_TITLE, WETH_ADDRESS, WETH_ADDRESS_ARB, WBNB_ADDRESS, ETH_ADDRESS
from bot.callback_factories.back import Back
from bot.callback_factories.start_action import StartAction
from bot.handlers.routers import start_menu
from bot.keyboards.menu_keyboard import ask_for_network, back_to_main_kb
from aiogram import F
from database.wallet_functions import get_active_network_wallet
from database.user_functions import get_user_by_chat_id
from bot.db_client import db

@start_menu.callback_query(StartAction.filter(F.type=="approve_balance"))
async def handle_token_approve(query: types.CallbackQuery, callback_data: CallbackData):
    text = "Please select the network for which you'd like to preapprove your balance 🌐 This will help you handle snipes faster ⚡ on the active wallet 🏦😄"
    await query.message.edit_text(text=text, reply_markup=ask_for_network("approve_wallet"))


@start_menu.callback_query(StartAction.filter(F.action=="approve_wallet"))
async def approve_wallet_balance(query: types.CallbackQuery, callback_data: CallbackData):
    network = callback_data.value
    user = await get_user_by_chat_id(query.from_user.id, db)
    user_wallet = await get_active_network_wallet(user, network, db)
    private_key = eth_wm.decrypt_seed(user_wallet.wallet_encrypted_seed)
    address = user_wallet.wallet_address
    if network=="ethereum":
        dex = eth_uni_m
        quote = eth_wm.web3.to_checksum_address(WETH_ADDRESS)
    elif network=="bsc":
        dex = None
        quote = eth_wm.web3.to_checksum_address(WBNB_ADDRESS)

    else:
        quote = eth_wm.web3.to_checksum_address(WETH_ADDRESS_ARB)
        dex = arb_uni_m
    dex.address = eth_wm.web3.to_checksum_address(address)
    if dex.get_eth_balance()>0:
        
        try:
            dex.private_key = private_key
            # dex.approve(quote)
            approval_message = f"Approval made on {network.upper()} network 🚀\n\n"
            # if network == "ethereum":
            #     tx_url = f"https://etherscan.io/tx/{resp.hex()}"
            # elif network == "bsc":
            #     tx_url = f"https://bscscan.com/tx/{resp.hex()}"
            # else:
            #     tx_url = f"https://arbiscan.io/tx/{resp.hex()}"
            # approval_message += f"🔗 Transaction link: {tx_url}"
            await query.answer()
            await query.message.edit_text(approval_message, reply_markup=back_to_main_kb())
        except Exception as e:
            print(f"Error in approving: {e}")
            await query.message.edit_text("There's an error in token approval. Please try later or report the issue.", reply_markup=back_to_main_kb())
    else:
        text = "Balance of your active wallet is zero."
        await query.message.edit_text(text, reply_markup=back_to_main_kb())


