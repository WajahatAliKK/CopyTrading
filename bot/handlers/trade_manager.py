from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.filters.callback_data import CallbackData
from bot.keyboards.menu_keyboard import manage_trade_keyboard

from bot.db_client import db

from database.user_functions import get_user, get_user_by_chat_id
from database.trade_functions import get_trades_by_user_id, delete_trade_by_id
from database.wallet_functions import get_active_network_wallet
from database.ca_functions import get_coin
from aiogram.filters import Command, StateFilter
from bot.utils.config import HOLDING_TOKEN_NAME, HOLDING_QUANTITY, ETH_FEE, GROUP_TITLE, ETH_ADDRESS, WETH_ADDRESS, WBNB_ADDRESS, WETH_ADDRESS_ARB
from bot.callback_factories.back import Back
from bot.callback_factories.start_action import StartAction
from bot.callback_factories.trades_manage import TradeAction
from bot.handlers.routers import start_menu
from aiogram import F
from bot.utils.get_trade_stats import get_pair_price, sell_trade, sell_all
from bot.keyboards.menu_keyboard import confirmation_keyboard, back_to_main_kb
from bot.callback_factories.confirmation_action import ConfirmAction
from bot.db_client import db
from bot.uniswap_utils import uniswap_base, sushiswap_base, pancakeswap_base
import datetime
from bot.kb_texts.all_messages import get_trade_message, no_open_trades, trade_sell_conf, sell_all_conf

import asyncio



@start_menu.callback_query(StartAction.filter(F.type=="manage_trades"))
async def open_trades_manager(query: types.CallbackQuery, callback_data: CallbackData):
    user = await get_user_by_chat_id(query.from_user.id, db)
    trades = await get_trades_by_user_id(user.id, db)
    if trades:
        current_trade = trades[0]
        if len(trades)>1:
            next_trade = trades[1].id
            last_trade = trades[-2].id
        else:
            next_trade = trades[0].id
            last_trade = trades[0].id
        if current_trade.network=="ethereum":
            dexx = uniswap_base
        elif current_trade.network=="bsc":
            dexx = pancakeswap_base
        else:
            dexx = sushiswap_base
        
        price = get_pair_price(current_trade.token_in_address, current_trade.token_address, current_trade.coin_dex)
        in_token = current_trade.token_in_address
        if current_trade.network.lower()=="ethereum":
            if in_token == ETH_ADDRESS:
                in_token = WETH_ADDRESS
        if current_trade.network.lower()=="bsc":
            if in_token == ETH_ADDRESS:
                in_token = WBNB_ADDRESS
        if current_trade.network.lower()=="arbitrum":
            if in_token == ETH_ADDRESS:
                in_token = WETH_ADDRESS_ARB
        coin = await get_coin((current_trade.token_address).lower(), db)
        if coin:
            pair_address = coin.lp_address
        else:
            pair_address = dexx.get_v2_pair_address(in_token, current_trade.token_address)
        kb = manage_trade_keyboard(current_trade, last_trade, next_trade,pair_address)
        try:
            reserves = dexx.get_v2_reserves(pair_address)
            if reserves[0]<reserves[1]:
                eth_liq = dexx.web3.from_wei(reserves[0],'ether')
                token_liq = dexx.web3.from_wei(reserves[1],'ether')
            else:
                eth_liq = dexx.web3.from_wei(reserves[1],'ether')
                token_liq = dexx.web3.from_wei(reserves[0],'ether')
        except:
            eth_liq = 0
            token_liq = 0
        wallet = await get_active_network_wallet(user, current_trade.network, db)
        if wallet:
            dexx.wallet = wallet.wallet_address
            balance = dexx.get_token_balance(current_trade.token_address)
            balance = balance/dexx.get_token_decimals(current_trade.token_address)
            if not current_trade.price_in:
                price_in = 0
            else:
                price_in = current_trade.price_in
            if price_in:
                pnl = (price_in - price)/price_in
            else:
                pnl = 0
            text = get_trade_message(current_trade, price, pnl, balance, eth_liq, token_liq)
            await query.message.edit_text(text=text, reply_markup=kb)
            await query.answer()
        else:
            await query.answer(text=no_open_trades)
    else:
        await query.answer(text=no_open_trades)



@start_menu.callback_query(TradeAction.filter(F.value=="next_coin"))
async def switch_trade_cb(query: types.CallbackQuery, callback_data: TradeAction):
    new_id = callback_data.trade_id
    user = await get_user_by_chat_id(query.from_user.id, db)
    trades = await get_trades_by_user_id(user.id, db)
    list_i = 0
    for i, trade in enumerate(trades):
        if trade.id == new_id:
            list_i = i
            break
    current_trade = trades[list_i]
    if list_i + 1 >= len(trades):
        list_i = -1
    if len(trades)>1:
        next_trade = trades[list_i+1].id
        last_trade = trades[list_i-1].id
    else:
        next_trade = trades[0].id
        last_trade = trades[0].id
    if current_trade.network=="ethereum":
        dexx = uniswap_base
    elif current_trade.network=="bsc":
        dexx = pancakeswap_base
    else:
        dexx = sushiswap_base
    
    price = get_pair_price(current_trade.token_in_address, current_trade.token_address, current_trade.coin_dex)
    in_token = current_trade.token_in_address
    if current_trade.network.lower()=="ethereum":
        if in_token == ETH_ADDRESS:
            in_token = WETH_ADDRESS
    if current_trade.network.lower()=="bsc":
        if in_token == ETH_ADDRESS:
            in_token = WBNB_ADDRESS
    if current_trade.network.lower()=="arbitrum":
        if in_token == ETH_ADDRESS:
            in_token = WETH_ADDRESS_ARB
    coin = await get_coin((current_trade.token_address).lower(), db)
    if coin:
        pair_address = coin.lp_address
    else:
        pair_address = dexx.get_v2_pair_address(in_token, current_trade.token_address)
    kb = manage_trade_keyboard(current_trade, last_trade, next_trade,pair_address)
    reserves = dexx.get_v2_reserves(pair_address)
    
    if reserves:
        if reserves[0]<reserves[1]:
            eth_liq = dexx.web3.from_wei(reserves[0],'ether')
            token_liq = dexx.web3.from_wei(reserves[1],'ether')
        else:
            eth_liq = dexx.web3.from_wei(reserves[1],'ether')
            token_liq = dexx.web3.from_wei(reserves[0],'ether')
    else:
        eth_liq = 0
        token_liq = 0

    wallet = await get_active_network_wallet(user, current_trade.network, db)
    dexx.wallet = wallet.wallet_address
    balance = dexx.get_token_balance(current_trade.token_address)
    balance = balance/dexx.get_token_decimals(current_trade.token_address)

    if not current_trade.price_in:
        price_in = 0
    else:
        price_in = current_trade.price_in
    if price_in:
        pnl = (price_in - price)/price_in
    else:
        pnl = 0
    text = get_trade_message(current_trade, price, pnl, balance, eth_liq, token_liq)
    await query.message.edit_text(text=text, reply_markup=kb)
    await query.answer()




@start_menu.callback_query(TradeAction.filter(F.value=="prev_coin"))
async def switch_trade_cb1(query: types.CallbackQuery, callback_data: TradeAction):
    new_id = callback_data.trade_id
    user = await get_user_by_chat_id(query.from_user.id, db)
    trades = await get_trades_by_user_id(user.id, db)
    list_i = 0
    for i, trade in enumerate(trades):
        if trade.id == new_id:
            list_i = i
            break
    current_trade = trades[list_i]
    if list_i + 1 >= len(trades):
        list_i = -1
    if len(trades)>1:
        next_trade = trades[list_i+1].id
        last_trade = trades[list_i-1].id
    else:
        next_trade = trades[0].id
        last_trade = trades[0].id
    if current_trade.network=="ethereum":
        dexx = uniswap_base
    elif current_trade.network=="bsc":
        dexx = pancakeswap_base
    else:
        dexx = sushiswap_base
    
    price = get_pair_price(current_trade.token_in_address, current_trade.token_address, current_trade.coin_dex)
    in_token = current_trade.token_in_address
    if current_trade.network.lower()=="ethereum":
        if in_token == ETH_ADDRESS:
            in_token = WETH_ADDRESS
    if current_trade.network.lower()=="bsc":
        if in_token == ETH_ADDRESS:
            in_token = WBNB_ADDRESS
    if current_trade.network.lower()=="arbitrum":
        if in_token == ETH_ADDRESS:
            in_token = WETH_ADDRESS_ARB
    coin = await get_coin((current_trade.token_address).lower(), db)
    if coin:
        pair_address = coin.lp_address
    else:
        pair_address = dexx.get_v2_pair_address(in_token, current_trade.token_address)
    kb = manage_trade_keyboard(current_trade, last_trade, next_trade,pair_address)
    reserves = dexx.get_v2_reserves(pair_address)
    if reserves:
        if reserves[0]<reserves[1]:
            eth_liq = dexx.web3.from_wei(reserves[0],'ether')
            token_liq = dexx.web3.from_wei(reserves[1],'ether')
        else:
            eth_liq = dexx.web3.from_wei(reserves[1],'ether')
            token_liq = dexx.web3.from_wei(reserves[0],'ether')
    else:
        eth_liq = 0
        token_liq = 0
    wallet = await get_active_network_wallet(user, current_trade.network, db)
    dexx.wallet = wallet.wallet_address
    balance = dexx.get_token_balance(current_trade.token_address)
    balance = balance/dexx.get_token_decimals(current_trade.token_address)
    if not current_trade.price_in:
        price_in = 0
    else:
        price_in = current_trade.price_in
    if price_in:
        pnl = (price_in - price)/price_in
    else:
        pnl = 0
    text = get_trade_message(current_trade, price, pnl, balance, eth_liq, token_liq)
    await query.message.edit_text(text=text, reply_markup=kb)
    await query.answer()


@start_menu.callback_query(TradeAction.filter(F.value=="refresh_stats"))
async def switch_trade_cb2(query: types.CallbackQuery, callback_data: TradeAction):
    new_id = callback_data.trade_id
    user = await get_user_by_chat_id(query.from_user.id, db)
    trades = await get_trades_by_user_id(user.id, db)
    list_i = 0
    for i, trade in enumerate(trades):
        if trade.id == new_id:
            list_i = i
            break
    current_trade = trades[list_i]
    if list_i + 1 > len(trades):
        list_i = -1
    if len(trades)>1:
        next_trade = trades[list_i+1].id
        last_trade = trades[list_i-1].id
    else:
        next_trade = trades[0].id
        last_trade = trades[0].id
    # next_trade = trades[list_i+1].id
    # last_trade = trades[list_i-1].id
    
    price = get_pair_price(current_trade.token_in_address, current_trade.token_address, current_trade.coin_dex)
    in_token = current_trade.token_in_address
    
    if current_trade.network.lower()=="ethereum":
        if in_token == ETH_ADDRESS:
            in_token = WETH_ADDRESS
    if current_trade.network.lower()=="bsc":
        if in_token == ETH_ADDRESS:
            in_token = WBNB_ADDRESS
    if current_trade.network.lower()=="arbitrum":
        if in_token == ETH_ADDRESS:
            in_token = WETH_ADDRESS_ARB
    if current_trade.network=="ethereum":
        dexx = uniswap_base
    elif current_trade.network=="bsc":
        dexx = pancakeswap_base
    else:
        dexx = sushiswap_base
    pair_address = dexx.get_v2_pair_address(in_token, current_trade.token_address)
    kb = manage_trade_keyboard(current_trade, last_trade, next_trade,pair_address)
    reserves = dexx.get_v2_reserves(pair_address)
    if reserves:
        if reserves[0]<reserves[1]:
            eth_liq = dexx.web3.from_wei(reserves[0],'ether')
            token_liq = dexx.web3.from_wei(reserves[1],'ether')
        else:
            eth_liq = dexx.web3.from_wei(reserves[1],'ether')
            token_liq = dexx.web3.from_wei(reserves[0],'ether')
    else:
        eth_liq = 0
        token_liq = 0
    wallet = await get_active_network_wallet(user, current_trade.network, db)
    dexx.wallet = wallet.wallet_address
    balance = dexx.get_token_balance(current_trade.token_address)
    balance = balance/dexx.get_token_decimals(current_trade.token_address)
    if not current_trade.price_in:
        price_in = 0
    else:
        price_in = current_trade.price_in
    if price_in:
        pnl = (price_in - price)/price_in
    else:
        pnl = 0
    text = get_trade_message(current_trade, price, pnl, balance, eth_liq, token_liq)
    await query.message.edit_text(text=text, reply_markup=kb)
    await query.answer()


@start_menu.callback_query(TradeAction.filter(F.value=="sell_now"), StateFilter('*'))
async def switch_trade_cb2(query: types.CallbackQuery, callback_data: TradeAction, state: FSMContext):
    new_id = callback_data.trade_id
    kb = confirmation_keyboard('sell_trade')
    text = trade_sell_conf
    await query.message.edit_text(text=text, reply_markup=kb)
    await query.answer()
    await state.set_data({"id":new_id})
    

@start_menu.callback_query(TradeAction.filter(F.value=="sell_all"), StateFilter('*'))
async def sell_all_cb(query: types.CallbackQuery, callback_data: TradeAction, state: FSMContext):
    new_id = callback_data.trade_id
    kb = confirmation_keyboard('sell_all_trades')
    text = sell_all_conf
    await query.message.edit_text(text=text, reply_markup=kb)
    await query.answer()

    await state.set_data({"id":new_id})



@start_menu.callback_query(ConfirmAction.filter(F.action=="sell_all_trades"), StateFilter('*'))
async def sell_confirm_all(query: types.CallbackQuery, callback_data: ConfirmAction, state: FSMContext):
    resp = callback_data.value
    if resp == "confirm":
        data = await state.get_data()
        id = data['id']
        user = await get_user_by_chat_id(query.from_user.id, db)
        trades = await get_trades_by_user_id(user.id, db)
        eth_wallet = await get_active_network_wallet(user, "ethereum", db)
        bsc_wallet = await get_active_network_wallet(user, "bsc", db)
        arb_wallet = await get_active_network_wallet(user, "arbitrum", db)
        # Notify the user that the process has been initiated
        await query.message.edit_text(text="Sell action has been initiated. Please wait...")
        eth_trades = [trade for trade in trades if trade.network=="ethereum"]
        bsc_trades = [trade for trade in trades if trade.network=="bsc"]
        arb_trades = [trade for trade in trades if trade.network=="arbitrum"]
        # Call sell_all function in a separate thread
        if eth_trades:
            sell_all_task = asyncio.create_task(sell_all(user, eth_trades, eth_wallet))
            await sell_all_task
        if bsc_trades:
            sell_all_task = asyncio.create_task(sell_all(user, bsc_trades, bsc_wallet))
            await sell_all_task
        if arb_trades:
            sell_all_task = asyncio.create_task(sell_all(user, arb_trades, arb_wallet))
            await sell_all_task

        await query.message.edit_text(text=f"🎉 Sale completed successfully! 🎉\n",reply_markup=back_to_main_kb())

        await query.message.edit_text(text=f"🎉 Sale completed successfully! 🎉\n",reply_markup=back_to_main_kb())
        
    else:
        await query.message.edit_text(text="❌ Sale action halted. No changes made. ❌",reply_markup=back_to_main_kb())



@start_menu.callback_query(ConfirmAction.filter(F.action=="sell_trade"), StateFilter('*'))
async def sell_confirm(query: types.CallbackQuery, callback_data: ConfirmAction, state: FSMContext):
    resp = callback_data.value
    if resp == "confirm":
        data = await state.get_data()
        id = data['id']
        user = await get_user_by_chat_id(query.from_user.id, db)
        trades = await get_trades_by_user_id(user.id, db)
        list_i = 0
        for i, trade in enumerate(trades):
            if trade.id == id:
                list_i = trade
                break
        wallet = await get_active_network_wallet(user, list_i.network, db)
        print(f"Sell initiated by: {wallet.wallet_address} | Trade id: {list_i.id}")
        await query.message.edit_text(text="🔄 Processing your sale... Hang tight! 🕐")

        # Call sell_all function in a separate thread
        sell_all_task = asyncio.create_task(sell_all(user, [list_i], wallet))

        # Wait for the sell_all_task to complete
        await sell_all_task
        status, hex1 = await sell_trade(user, list_i, wallet)
        if status:
            await query.message.edit_text(text=f"Sold!!.\nTransaction Hash: {hex1}",reply_markup=back_to_main_kb())
        else:
            await query.message.edit_text(text=f"Error while selling.\n Error Message: {hex1}",reply_markup=back_to_main_kb())
        
    else:
        await query.message.edit_text(text="Sell action has been cancelled.",reply_markup=back_to_main_kb())

@start_menu.callback_query(TradeAction.filter(F.value=="delete"), StateFilter('*'))
async def delete_trade(query: types.CallbackQuery, callback_data: ConfirmAction, state: FSMContext):
    new_id = callback_data.trade_id
    kb = confirmation_keyboard('delete_trade')
    text = "‼️ You sure you want to delete this trade? ‼️"
    await query.message.edit_text(text=text, reply_markup=kb)
    await query.answer()
    await state.set_data({"id":new_id})



@start_menu.callback_query(ConfirmAction.filter(F.action=="delete_trade"), StateFilter('*'))
async def delete_trade_confirm(query: types.CallbackQuery, callback_data: ConfirmAction, state: FSMContext):
    resp = callback_data.value
    if resp == "confirm":
        id = await state.get_data()
        trade = await delete_trade_by_id(id['id'], db)
        await query.answer(text="Trade has been deleted.")
        await open_trades_manager(query, callback_data)
    else:
        await query.answer(text="Alright! It's cancelled.")
        await open_trades_manager(query, callback_data)