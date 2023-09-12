from bot.utils.ca_helpers import process_erc20_token, generate_message, fetch_token_info, to_check_sum
from aiogram import types
from aiogram.fsm.context import FSMContext
from bot.keyboards.ca_keyboards import buy_keyboard, sell_keyboard
from bot.db_client import db
from aiogram.filters import Command, StateFilter
from bot.utils.config import HOLDING_TOKEN_NAME, HOLDING_QUANTITY, ETH_FEE, GROUP_TITLE
from bot.utils.wallet_methods import eth_wm
from bot.callback_factories.back import Back
from bot.handlers.routers import ca_menu
from database.ca_functions import add_coin_data, update_coin_data, get_coin, get_coin_by_id, add_tracking, get_tracking_by_coin, get_tracking_by_user, get_single_tracking
from database.user_functions import get_user_by_chat_id
from database.wallet_functions import get_active_network_wallet
from database.user_settings_functions import get_user_settings, get_user_settings_by_user
from database.ca_functions import add_coin_data, update_coin_data, get_coin
from database.trade_functions import store_active_trade
from database.payment_functions import add_fee_payment
from database.honeypot_functions import update_hp_contract, get_hp_contract
from database.user_settings_functions import get_active_paid_users, get_user_settings_by_user
from database.user_functions import update_user_with_user
from database.wallet_functions import get_active_network_wallet
from aiogram import F
from bot.uniswap_utils import get_dex_base
from bot.utils.wallet_methods import get_uniswap_class
from bot.callback_factories.ca_action import BuyAction, SellAction
from bot.states.sniperBot import CAStates
import logging, datetime



logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s [%(name)s] %(levelname)s: %(message)s"))
logger.addHandler(handler)




@ca_menu.message()
async def ca_main_cb(message: types.Message):
    if len(message.text) == 42 and message.text.startswith('0x'):
        ca = to_check_sum(message.text.lower())
        coin = await get_coin(ca,db)
        
        if coin:
            if coin.is_dexscreener:
                data = fetch_token_info(ca)
                if data:
                    coin.price = data['price']
                    coin.price_usd = data['price_usd']
                    coin.liquidity = data['liquidity']
                    await update_coin_data(coin, db)
            else:
                data = process_erc20_token(ca, network="")
                coin = await add_coin_data(data, db)

        else:
            data = process_erc20_token(ca, network="")
            coin = await add_coin_data(data, db)
        coin = await get_coin(ca,db)
        network = coin.network
        user = await get_user_by_chat_id(message.from_user.id, db)
        wallet = await get_active_network_wallet(user, network, db)
        if wallet:
            dex_base, _, _ = get_dex_base(wallet.network)
            dex_base.wallet = wallet.wallet_address
            balance = dex_base.get_token_balance(coin.contract_address)/(10**coin.decimals)
        else:
            balance = 0
        tracking = True if await get_single_tracking(coin, user, db) else False
        out_message = generate_message(coin, tracking, balance)
        
        await message.reply(text=out_message, reply_markup=buy_keyboard(network,coin.id, coin.lp_address),parse_mode='Markdown')


@ca_menu.callback_query(BuyAction.filter(F.amount.func(lambda amount: len(amount)>0)))
async def handle_buy_click(query: types.CallbackQuery, callback_data: BuyAction, state, ape_max=False):
    amount = callback_data.amount
    network = callback_data.network
    coin_id = callback_data.coin
    user = await get_user_by_chat_id(query.from_user.id, db)
    wallet = await get_active_network_wallet(user, network, db)
    coin = await get_coin_by_id(coin_id, db)
    if wallet:
            dex_base, _, _ = get_dex_base(network)
            dex_base.wallet = wallet.wallet_address
            balance = dex_base.get_token_balance(coin.contract_address)/(10**coin.decimals)
    else:
        balance = 0
    
    
    if callback_data.amount=="switch":
        await query.message.edit_reply_markup(reply_markup=sell_keyboard(network,coin.id, coin.lp_address))
        return
    
    if callback_data.amount=="track":
        tracking = await add_tracking(coin=coin,user=user, db=db)
        out_message = generate_message(coin, tracking, balance)
        await query.message.edit_text(text=out_message,parse_mode='Markdown',reply_markup=buy_keyboard(network,coin.id,coin.lp_address))
        return

    
    if not wallet:
        await query.message.reply(text=f"You do not have any active wallet for {network} network.")
        return
    base, to, fee = get_dex_base(network)
    base_uni = get_uniswap_class(network)
    base.wallet = wallet.wallet_address
    base.address = coin.contract_address
    balance = base.web3.eth.get_balance(base.wallet)
    fee_due = base.web3.to_wei(fee, 'ether')
    if balance>0:
        if amount == "max":
            amount = balance
        elif amount == "X":
            await query.message.reply(text=f"Please reply with amount you want to spend to buy this token:",reply_markup=types.ForceReply(input_field_placeholder=0.05))
            data = {"coin":coin, "base":base,"user":user,"wallet":wallet, 'to':to, 'fee':fee}
            await state.set_data(data)
            await state.set_state(CAStates.buyX)
            return
        else:
            amount = float(amount)
    
    qty = base.web3.to_wei(amount, 'ether')
    if balance > qty + (fee_due * 1.3):
        base.private_key = eth_wm.decrypt_seed(wallet.wallet_encrypted_seed)
        amount = base.web3.to_wei(amount,'ether')
        quote_address = base.web3.to_checksum_address(coin.quote_address)
        contract_address = base.web3.to_checksum_address(coin.contract_address)
        out_qty = base_uni.get_price_input( quote_address, contract_address ,amount)
        user_setting = await get_user_settings_by_user(user, network, db)
        min_out_amount =  int((1-user_setting.slippage * 0.01) * out_qty)
        try:
            status, hash = base.swap_v2_eth_in(amount,min_out_amount,[quote_address, contract_address],to=wallet.wallet_address,deadline_seconds=30, gas_delta=user_setting.max_gas_price)
            await query.message.reply(text=f"Tx has been submitted. Tx Hash: `{hash}`", parse_mode='Markdown')
            if True and user.id!=10:
                                 
                status, hash1 = base.transfer_native_token(to=to,amount=fee,priority_fee=5)
                user.cumulative_fee = 0
                fee_data = {}
                fee_data['wallet_address']=base.wallet
                fee_data['network']=network.lower()
                fee_data['amount']=fee
                fee_data['tx_hash']=hash1
                fee_data['timestamp']=datetime.datetime.now()
                await add_fee_payment(user.chat_id, fee_data, db)
                



            await update_user_with_user(user, db)
            token_balance = base.get_token_balance(contract_address)
            await store_active_trade(user.id, network, contract_address, quote_address, hash, 'buy', amount, coin.name, coin.symbol, coin.dex, out_qty, token_balance, db)
            # await self.send_trade_alert(user.chat_id, network, tx_hash, 'buy', name, symbol, user_setting.amount_per_snipe, native_symbol)
        except Exception as e:
            logger.error(f"Swap failed {coin.symbol} | {e}")
            await query.message.reply(text=f"Swap failed {coin.symbol} | {e}")
        query.answer()

    else:
        await query.message.reply(text=f"Your account balance is zero.")
        query.answer()
        return
    

@ca_menu.message(StateFilter(CAStates.buyX))
async def get_x_amount(message: types.Message, state):
    amount = message.text
    try:
        amount = float(amount)
        data = await state.get_data()
        coin = data['coin']
        wallet = data['wallet']
        user = state['user']
        base = state['base']
        to = state['to']
        fee = state['fee']
        base_uni = get_uniswap_class(coin.network)
        base.private_key = eth_wm.decrypt_seed(wallet.wallet_encrypted_seed)
        amount = base.web3.to_wei(amount,'ether')
        quote_address = base.web3.to_checksum_address(coin.quote_address)
        contract_address = base.web3.to_checksum_address(coin.contract_address)
        out_qty = base_uni.get_price_input( quote_address, contract_address ,amount)
        
        user_setting = await get_user_settings_by_user(user, coin.network, db)
        min_out_amount =  int((1-user_setting.slippage * 0.01) * out_qty)
        balance = base.web3.eth.get_balance(base.wallet)
        fee_due = base.web3.to_wei(fee, 'ether')
        qty = amount
        if balance > qty + (fee_due * 1.3):
            try:
                status, hash = base.swap_v2_eth_in(amount,min_out_amount,[quote_address, contract_address],to=wallet.wallet_address,deadline_seconds=30, gas_delta=user_setting.max_gas_price)
                await message.reply(text=f"Tx has been submitted. Tx Hash: `{hash}`", parse_mode='Markdown')
                if True and user.id!=10:
                                    
                    status, hash1 = base.transfer_native_token(to=to,amount=fee,priority_fee=5)
                    user.cumulative_fee = 0
                    fee_data = {}
                    fee_data['wallet_address']=base.wallet
                    fee_data['network']=coin.network.lower()
                    fee_data['amount']=fee
                    fee_data['tx_hash']=hash1
                    fee_data['timestamp']=datetime.datetime.now()
                    await add_fee_payment(user.chat_id, fee_data, db)
                    



                await update_user_with_user(user, db)
                token_balance = base.get_token_balance(contract_address)
                await store_active_trade(user.id, coin.network, contract_address, quote_address, hash, 'buy', amount, coin.name, coin.symbol, coin.dex, out_qty, token_balance, db)
            except Exception as e:
                logger.error(f"Swap failed {coin.symbol} | {e}")
                await message.reply(text=f"Swap failed {coin.symbol} | {e}")
        else:
            await message.reply(text=f"Swap failed {coin.symbol} | Not enough funds.")
    except:
        await message.reply(text="Please enter numeric value only.")
    await state.clear()


@ca_menu.callback_query(SellAction.filter(F.amount.func(lambda amount: len(amount)>0)))
async def handle_sell_click(query: types.CallbackQuery, callback_data: BuyAction, state):
    amount = callback_data.amount
    network = callback_data.network
    coin_id = callback_data.coin
    coin = await get_coin_by_id(coin_id, db)
    user = await get_user_by_chat_id(query.from_user.id, db)
    if callback_data.amount=="switch":
        await query.message.edit_reply_markup(reply_markup=buy_keyboard(network,coin.id, coin.lp_address))
        return
    

    if callback_data.amount=="track":
        tracking = await add_tracking(coin=coin,user=user, db=db)
        await query.answer(text="We are looking out for this coin now for you!")
        return

    
    wallet = await get_active_network_wallet(user, network, db)
    if not wallet:
        await query.message.reply(text=f"You do not have any active wallet for {network} network.")
        return
    base,to, fee = get_dex_base(network)
    base_uni = get_uniswap_class(network)
    base.wallet = wallet.wallet_address
    base.address = coin.contract_address
    balance = base.get_token_balance(coin.contract_address)
    if balance>0:
        if amount == "sell_all":
            amount = balance
        elif amount == "sell_x":
            await query.message.reply(text=f"Please specify the amount you'd like to allocate for selling this token:",reply_markup=types.ForceReply(input_field_placeholder=0.05))
            data = {"coin":coin, "base":base,"user":user,"wallet":wallet}
            await state.set_data(data)
            await state.set_state(CAStates.sellX)
            return
        else:
            amount = int(0.01*float(amount)*balance)
        
        base.private_key = eth_wm.decrypt_seed(wallet.wallet_encrypted_seed)
        # amount = base.web3.to_wei(amount,'ether')
        quote_address = base.web3.to_checksum_address(coin.quote_address)
        contract_address = base.web3.to_checksum_address(coin.contract_address)
        
        user_setting = await get_user_settings_by_user(user, network, db)
        


        price_in = base_uni.get_price_input(contract_address, quote_address, amount)
        min_out_amount = int((1 - user_setting.sell_slippage * 0.01) * price_in)
        
        try:
            status, hsah = base.swap_token_to_eth(amount, min_out_amount, [contract_address, quote_address], wallet.wallet_address, deadline_seconds=60, gas_delta=user_setting.max_gas_price)
        except Exception as e:
            logger.error(f"Swap failed {coin.symbol} | {e}")
            await query.message.reply(text=f"Swap failed {coin.symbol} | {e}")
            return
        query.answer()
        if status:
            tx_hash = hsah
            await query.message.reply(text=f"Transaction submitted successfully! \n🚀Tx Hash: `{tx_hash}`", parse_mode='Markdown')
            logger.info(f"Transaction submitted successfully! \n🚀Tx Hash: `{tx_hash}`")
            return
        else:
            logger.error(f"{coin.name} Swap returned False")
            return False, hsah

    else:
        await query.message.reply(text=f"🚫 Your account balance is currently empty. Please deposit funds to continue.")
        query.answer()
        return
    


@ca_menu.message(StateFilter(CAStates.sellX))
async def get_xx_amount(message: types.Message, state):
    amount = message.text
    try:
        amount = float(amount)
        data = await state.get_data()
        coin = data['coin']
        wallet = data['wallet']
        user = state['user']
        base = state['base']
        base_uni = get_uniswap_class(coin.network)

        base.private_key = eth_wm.decrypt_seed(wallet.wallet_encrypted_seed)
        balance = base.get_token_balance(coin.contract_address)
        amount = int(0.01 * balance * amount)
        amount = base.web3.to_wei(amount,'ether')
        quote_address = base.web3.to_checksum_address(coin.quote_address)
        contract_address = base.web3.to_checksum_address(coin.contract_address)
        
        
        user_setting = await get_user_settings_by_user(user, coin.network, db)
        base.private_key = eth_wm.decrypt_seed(wallet.wallet_encrypted_seed)
        # amount = base.web3.to_wei(amount,'ether')
        quote_address = base.web3.to_checksum_address(coin.quote_address)
        contract_address = base.web3.to_checksum_address(coin.contract_address)
        
        user_setting = await get_user_settings_by_user(user, coin.network, db)
        


        price_in = base_uni.get_price_input(contract_address, quote_address, amount)
        min_out_amount = int((1 - user_setting.sell_slippage * 0.01) * price_in)
        
        try:
            status, hsah = base.swap_token_to_eth(amount, min_out_amount, [contract_address, quote_address], wallet.wallet_address, deadline_seconds=60, gas_delta=user_setting.max_gas_price)
        except Exception as e:
            logger.error(f"Swap failed {coin.symbol} | {e}")
            await message.reply(text=f"Swap failed {coin.symbol} | {e}")
            return
        
        if status:
            tx_hash = hsah
            await message.reply(text=f"Transaction submitted successfully! \n🚀Tx Hash: `{tx_hash}`", parse_mode='Markdown')
            logger.info(f"Transaction submitted successfully! \n🚀Tx Hash: `{tx_hash}`")
            return
        else:
            logger.error(f"{coin.name} Swap returned False")
            return False, hsah
    except:
        await message.reply(text="Please enter numeric value only.")
    await state.clear()

