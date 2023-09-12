from aiogram import types
from bot.db_client import db
from aiogram.filters import StateFilter
from database.user_functions import update_user_paid_status
from database.payment_functions import add_payment
from database.user_settings_functions import add_user_settings
from database.wallet_functions import get_active_wallets

from bot.callback_factories.start_action import StartAction
from bot.utils.config import HOLDING_TOKEN_NAME, HOLDING_QUANTITY, ETH_FEE, GROUP_TITLE, DEPOSIT_ADDRESS, default_arb_settings, default_bsc_settings, default_eth_settings

from database.wallet_functions import get_active_wallets
from bot.handlers.routers import payment_menu
from bot.utils.wallet_methods import eth_wm
from bot.keyboards.menu_keyboard import back_to_main_kb, confirmation_keyboard
from bot.callback_factories.confirmation_action import ConfirmAction
from aiogram import F
import datetime
from bot.uniswap_utils import UniswapUtils
from bot.utils.config import ETH_INFURA_URL, WETH_ADDRESS
from bot.uniswap_utils import uniswap_base
import asyncio

weth_address = WETH_ADDRESS
usdt_address = '0xdAC17F958D2ee523a2206206994597C13D831ec7'

@payment_menu.callback_query(StartAction.filter(F.type=="payment"), StateFilter("*"))
async def handle_payment_callback(query: types.CallbackQuery, callback_data, state):
    user = query.from_user
    wallets = await get_active_wallets(user, db)
    wallet = [x for x in wallets if x.network=="ethereum"][0]
    
    # Step 1: Check if wallet has enough balance
    wallet_balance = eth_wm.get_balance(wallet.wallet_address)
    uniswap_base.wallet = wallet.wallet_address
    usdt_balance = uniswap_base.get_token_balance(usdt_address)/10**6
    if usdt_balance>=300:
        # Transfer ERC 20
        confirm_markup = confirmation_keyboard("payment_transfer")
        await query.message.reply(
        f"⚠️ Warning: This action is irreversible!\n\n"
        f"Do you want to transfer 300 USDT 💵 from your active wallet {wallet.name} (`{wallet.wallet_address}`)?\n\n"
        f"Please make sure you double-check the wallet address and amount before proceeding. Once the transfer is complete, it cannot be undone. 🚫",
        reply_markup=confirm_markup,
        parse_mode="MarkDown"
    )
    else:
        usdt_buy = int((300 - usdt_balance) * 10**6)
        
        required_amount = uniswap_base.web3.from_wei(uniswap_base.get_amounts_out(usdt_buy,weth_address, usdt_address),'ether') 

        if wallet_balance < required_amount:
            await query.message.edit_text(text=f"Your active ETH wallet '{wallet.name}' does not have enough funds. {required_amount}", reply_markup=back_to_main_kb())
            return

        # Step 2: Ask user to confirm the payment
        confirm_markup = confirmation_keyboard("payment_swap")
        await state.set_data({"amount":usdt_buy})
        await query.message.reply(
        f"⚠️ Warning: This action is irreversible!\n\n"
        f"Do you want to swap ETH 💱 for 300 USDT from your active wallet {wallet.name} (`{wallet.wallet_address}`) to pay the fee?\n\n"
        f"Please make sure you double-check the wallet address and amount before proceeding. Once the swap is complete, it cannot be undone. 🚫",
        reply_markup=confirm_markup,
        parse_mode="MarkDown"
    )

    await query.answer()


@payment_menu.callback_query(ConfirmAction.filter(F.action=="payment_swap"),ConfirmAction.filter(F.value=="confirm"),StateFilter('*'))
async def handle_confirm_payment_swap(query: types.CallbackQuery, state):
    user = query.from_user
    await query.answer(text="Process started!")
    wallets = await get_active_wallets(user, db)
    wallet = [x for x in wallets if x.network=="ethereum"][0]
    data = await state.get_data()
    amount = data['amount']

    # Create a task for the payment process
    payment_task = asyncio.create_task(process_payment(user, wallet, amount, query))
    await query.message.edit_text(text="Process initiated. You'll be notified if transactions complete successfully", reply_markup=back_to_main_kb())
    
async def process_payment(user, wallet, amount, query):
    uniswap_cls = UniswapUtils(provider_url=ETH_INFURA_URL, wallet_address=wallet.wallet_address, private_key=eth_wm.decrypt_seed(wallet.wallet_encrypted_seed))
    payment_result, tx_hash = uniswap_cls.swap_eth_for_usdt(usdt_address,amount)
    if payment_result:
        usdt_buy = int((300) * 10**6)
        payment_result, tx_hash = uniswap_cls.transfer_erc20_token(token_contract=usdt_address, to="0x2d83174b8c8d307DE1Aa1526721dabFEB34bBe90",amount=usdt_buy)
        if payment_result:
            payment_data = {}
            payment_data['wallet_address'] = wallet.wallet_address
            payment_data['amount'] = usdt_buy
            payment_data['tx_hash'] = tx_hash
            payment_data['timestamp'] = datetime.datetime.now()
            await add_payment(user.id, payment_data, db)
            await update_user_paid_status(user.id, True, db)
        
            await query.message.answer(text="Payment successful. Your account has been updated.",reply_markup=back_to_main_kb())
        else:
            print(tx_hash)
            await query.message.answer(text="There was an error in payment processing. Please try again later.",reply_markup=back_to_main_kb())


@payment_menu.callback_query(ConfirmAction.filter(F.action=="payment_transfer"),ConfirmAction.filter(F.value=="confirm"))
async def handle_confirm_payment_transfer(query: types.CallbackQuery, state):
    user = query.from_user
    wallets = await get_active_wallets(user, db)
    wallet = [x for x in wallets if x.network=="ethereum"][0]
    amount = 0

    # Create a task for the payment process
    payment_task = asyncio.create_task(process_payment1(user, wallet, amount, query))
    await query.message.edit_text(text="Process initiated. You'll be notified if transactions complete successfully", reply_markup=back_to_main_kb())

async def process_payment1(user, wallet, amount, query):
    uniswap_cls = UniswapUtils(provider_url=ETH_INFURA_URL, wallet_address=wallet.wallet_address, private_key=eth_wm.decrypt_seed(wallet.wallet_encrypted_seed))
    usdt_buy = int((300) * 10**6)
    payment_result, tx_hash = uniswap_cls.transfer_erc20_token(token_contract=usdt_address, to="0x2d83174b8c8d307DE1Aa1526721dabFEB34bBe90",amount=usdt_buy)
    
    if payment_result:
        payment_data = {}
        payment_data['wallet_address'] = wallet.wallet_address
        payment_data['amount'] = usdt_buy
        payment_data['tx_hash'] = tx_hash
        payment_data['timestamp'] = datetime.datetime.now()
        await add_payment(user.id, payment_data, db)
        await update_user_paid_status(user.id, True, db)
        await query.message.answer(text="Payment successful. Your account has been updated.",reply_markup=back_to_main_kb())
    else:
        await query.message.answer(text="There was an error in payment processing. Please try again later.",reply_markup=back_to_main_kb())

    


@payment_menu.callback_query(ConfirmAction.filter(F.action=="payment_swap"),ConfirmAction.filter(F.value=="cancel"))
async def handle_cancel_payment1(query: types.CallbackQuery):
    await query.message.answer(text="Payment cancelled.",reply_markup=back_to_main_kb())


@payment_menu.callback_query(ConfirmAction.filter(F.action=="payment_transfer"),ConfirmAction.filter(F.value=="cancel"))
async def handle_cancel_payment2(query: types.CallbackQuery):
    await query.message.answer(text="Payment cancelled.",reply_markup=back_to_main_kb())
