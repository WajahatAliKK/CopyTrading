from aiogram import types
from bot.db_client import db
from aiogram.filters import StateFilter


from bot.callback_factories.start_action import StartAction
from bot.utils.config import HOLDING_TOKEN_NAME, HOLDING_QUANTITY, ETH_FEE, WETH_ADDRESS, DEPOSIT_ADDRESS, default_arb_settings, default_bsc_settings, default_eth_settings, ETH_ADDRESS

from database.wallet_functions import get_active_wallets
from bot.handlers.routers import payment_menu
from bot.utils.wallet_methods import eth_wm, eth_uni_m
from bot.keyboards.menu_keyboard import back_to_main_kb, confirmation_keyboard
from bot.callback_factories.confirmation_action import ConfirmAction
from aiogram import F

from bot.uniswap_utils import UniswapUtils, uniswap_base
from bot.utils.config import ETH_INFURA_URL, HOLDING_TOKEN_ADDRESS
import datetime
from database.holding_token_functions import add_holding_buy
from database.user_functions import update_user_holdT_status

@payment_menu.callback_query(StartAction.filter(F.type=="hold_tokens"), StateFilter("*"))
async def handle_payment_callback(query: types.CallbackQuery, callback_data):
    user = query.from_user
    wallets = await get_active_wallets(user, db)
    wallet = [x for x in wallets if x.network=="ethereum"][0]
    
    # Step 1: Check if wallet has enough balance
    wallet_balance = eth_wm.get_balance(wallet.wallet_address)
    required_amount = uniswap_base.calculate_v2_price(HOLDING_TOKEN_ADDRESS, WETH_ADDRESS) * HOLDING_QUANTITY
    token_name = uniswap_base.get_token_symbol(HOLDING_TOKEN_ADDRESS)
    if wallet_balance < required_amount:
        await query.message.edit_text(text=f"Your active ETH wallet '{wallet.name}' does not have enough funds.", reply_markup=back_to_main_kb())
        return

    # Step 2: Ask user to confirm the payment
    confirm_markup = confirmation_keyboard("hold_tokens")

    await query.message.reply(
        f"⚠️ Warning: This action is irreversible!\n\n"
        f"Do you want to swap {required_amount} ETH 💰 from your active wallet {wallet.name} (`{wallet.wallet_address}`) for {HOLDING_QUANTITY} units of {token_name}? 🔄\n\n"
        f"Please make sure you double-check the wallet address and amount before proceeding. Once the swap is complete, it cannot be undone. 🚫",
        reply_markup=confirm_markup,
        parse_mode="MarkDown"
    )

    await query.answer()


@payment_menu.callback_query(ConfirmAction.filter(F.action=="hold_tokens"),ConfirmAction.filter(F.value=="confirm"))
async def handle_confirm_payment(query: types.CallbackQuery):
    user = query.from_user
    wallets = await get_active_wallets(user, db)
    wallet = [x for x in wallets if x.network=="ethereum"][0]

    
    uniswap_base.wallet = wallet.wallet_address
    required_amount = uniswap_base.web3.to_wei(uniswap_base.calculate_v2_price(HOLDING_TOKEN_ADDRESS, WETH_ADDRESS) * HOLDING_QUANTITY * 1.0415, "ether")
    # required_amount = uniswap_base.web3.to_wei(uniswap_base.calculate_v2_price(WETH_ADDRESS, HOLDING_TOKEN_ADDRESS) * HOLDING_QUANTITY, "ether")

    weth_balance = uniswap_base.get_token_balance(WETH_ADDRESS)
    # print(f"WETH balance: {weth_balance}")

    # Swap ETH for Token X
    amount_in = required_amount
    eth_uni_m.private_key = eth_wm.decrypt_seed(wallet.wallet_encrypted_seed)
    eth_uni_m.default_slippage = 0.1
    try:
        eth_uni_m.address = wallet.wallet_address
        # eth_uni_m.approve(ETH_ADDRESS)
        trade = eth_uni_m.make_trade(ETH_ADDRESS, HOLDING_TOKEN_ADDRESS, amount_in)

        tx_hash = (trade.hex())
    except Exception as e:
        print(f"Error in buying hold token: {e}")
    # tx_hash = '0x'
    swap_result = True
    # amount_out_min = int(HOLDING_QUANTITY * (10 ** uniswap_base.get_token_decimals(HOLDING_TOKEN_ADDRESS)) * 0.90)  # 1% slippage
    # path = [uniswap_base.web3.to_checksum_address(WETH_ADDRESS), uniswap_base.web3.to_checksum_address(HOLDING_TOKEN_ADDRESS)]
    # to = wallet.wallet_address
    # deadline = int(uniswap_base.web3.eth.get_block('latest')['timestamp']) + 600  # 10 minutes from now

    # uniswap_base.private_key = eth_wm.decrypt_seed(wallet.wallet_encrypted_seed)
    # uniswap_base.approve(WETH_ADDRESS,amount_in)
    # # swap_result, tx_hash = uniswap_base.swap_v2(amount_in=amount_in, amount_out_min=amount_out_min, path=path, to=to, deadline=deadline)
    # swap_result, tx_hash = True, "0x"

    if swap_result:
        data = {
            "wallet_address": wallet.wallet_address,
            "timestamp": datetime.datetime.now(),
            "token_address": HOLDING_TOKEN_ADDRESS,
            "amount" : HOLDING_QUANTITY,
            "tx_hash": tx_hash
        }
        await add_holding_buy(user.id, data, db)
        # await update_user_holdT_status(user.id, True, db)
        await query.message.answer(text="Swap successful. Your account has been updated.",reply_markup=back_to_main_kb())
    else:
        await query.message.answer(text="There was an error in the swap operation. Please try again later.",reply_markup=back_to_main_kb())

@payment_menu.callback_query(ConfirmAction.filter(F.action=="hold_tokens"),ConfirmAction.filter(F.value=="cancel"))
async def handle_cancel_payment(query: types.CallbackQuery):
    await query.message.answer(text="Swap operation cancelled.",reply_markup=back_to_main_kb())




@payment_menu.callback_query(StartAction.filter(F.type=="hold_half_tokens"), StateFilter("*"))
async def handle_payment_callback(query: types.CallbackQuery, callback_data):
    user = query.from_user
    wallets = await get_active_wallets(user, db)
    wallet = [x for x in wallets if x.network=="ethereum"][0]
    
    # Step 1: Check if wallet has enough balance
    wallet_balance = eth_wm.get_balance(wallet.wallet_address)
    required_amount = uniswap_base.calculate_v2_price(HOLDING_TOKEN_ADDRESS, WETH_ADDRESS) * 2000
    token_name = uniswap_base.get_token_symbol(HOLDING_TOKEN_ADDRESS)
    if wallet_balance < required_amount:
        await query.message.edit_text(text=f"Your active ETH wallet '{wallet.name}' does not have enough funds.", reply_markup=back_to_main_kb())
        return

    # Step 2: Ask user to confirm the payment
    confirm_markup = confirmation_keyboard("hold_half_tokens")

    await query.message.reply(
        f"⚠️ Warning: This action is irreversible!\n\n"
        f"Do you want to swap {required_amount} ETH 💰 from your active wallet {wallet.name} (`{wallet.wallet_address}`) for 2000 units of {token_name}? 🔄\n\n"
        f"Please make sure you double-check the wallet address and amount before proceeding. Once the swap is complete, it cannot be undone. 🚫",
        reply_markup=confirm_markup,
        parse_mode="MarkDown"
    )

    await query.answer()


@payment_menu.callback_query(ConfirmAction.filter(F.action=="hold_half_tokens"),ConfirmAction.filter(F.value=="confirm"))
async def handle_confirm_payment(query: types.CallbackQuery):
    user = query.from_user
    wallets = await get_active_wallets(user, db)
    wallet = [x for x in wallets if x.network=="ethereum"][0]

    
    uniswap_base.wallet = wallet.wallet_address
    required_amount = uniswap_base.web3.to_wei(uniswap_base.calculate_v2_price(HOLDING_TOKEN_ADDRESS, WETH_ADDRESS) * 2000 * 1.0415, "ether")
    # required_amount = uniswap_base.web3.to_wei(uniswap_base.calculate_v2_price(WETH_ADDRESS, HOLDING_TOKEN_ADDRESS) * HOLDING_QUANTITY, "ether")

    weth_balance = uniswap_base.get_token_balance(WETH_ADDRESS)
    # print(f"WETH balance: {weth_balance}")

    # Swap ETH for Token X
    amount_in = required_amount
    eth_uni_m.private_key = eth_wm.decrypt_seed(wallet.wallet_encrypted_seed)
    eth_uni_m.default_slippage = 0.1
    try:
        eth_uni_m.address = wallet.wallet_address
        # eth_uni_m.approve(ETH_ADDRESS)
        trade = eth_uni_m.make_trade(ETH_ADDRESS, HOLDING_TOKEN_ADDRESS, amount_in)

        tx_hash = (trade.hex())
    except Exception as e:
        print(f"Error in buying hold token: {e}")
    # tx_hash = '0x'
    swap_result = True
    # amount_out_min = int(HOLDING_QUANTITY * (10 ** uniswap_base.get_token_decimals(HOLDING_TOKEN_ADDRESS)) * 0.90)  # 1% slippage
    # path = [uniswap_base.web3.to_checksum_address(WETH_ADDRESS), uniswap_base.web3.to_checksum_address(HOLDING_TOKEN_ADDRESS)]
    # to = wallet.wallet_address
    # deadline = int(uniswap_base.web3.eth.get_block('latest')['timestamp']) + 600  # 10 minutes from now

    # uniswap_base.private_key = eth_wm.decrypt_seed(wallet.wallet_encrypted_seed)
    # uniswap_base.approve(WETH_ADDRESS,amount_in)
    # # swap_result, tx_hash = uniswap_base.swap_v2(amount_in=amount_in, amount_out_min=amount_out_min, path=path, to=to, deadline=deadline)
    # swap_result, tx_hash = True, "0x"

    if swap_result:
        data = {
            "wallet_address": wallet.wallet_address,
            "timestamp": datetime.datetime.now(),
            "token_address": HOLDING_TOKEN_ADDRESS,
            "amount" : 2000,
            "tx_hash": tx_hash
        }
        await add_holding_buy(user.id, data, db)
        # await update_user_holdT_status(user.id, True, db)
        await query.message.answer(text="Swap successful. Your account has been updated.",reply_markup=back_to_main_kb())
    else:
        await query.message.answer(text="There was an error in the swap operation. Please try again later.",reply_markup=back_to_main_kb())

@payment_menu.callback_query(ConfirmAction.filter(F.action=="hold_half_tokens"),ConfirmAction.filter(F.value=="cancel"))
async def handle_cancel_payment(query: types.CallbackQuery):
    await query.message.answer(text="Swap operation cancelled.",reply_markup=back_to_main_kb())

