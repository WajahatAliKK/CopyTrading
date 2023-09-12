from telethon import TelegramClient, events
import re
import threading


import asyncio
import logging
from web3 import Web3
from bot.uniswap_utils import UniswapUtils 
import random
from bot.utils.config import BOT_TOKEN ,GROUP_CHAT_ID, WETH_ADDRESS, WETH_ADDRESS_ARB, WBNB_ADDRESS, ETH_ADDRESS, ADMIN_CHAT_ID, PER_TX_FEE, FEE_CUTOFF, ETH_FEE_WALLET, BSC_FEE_WALLET, ARB_FEE_WALLET
from bot.utils.get_trade_stats  import get_pair_price
# from bot.app import bot
from bot.utils.wallet_methods import eth_uni_m, eth_uni_mv3, arb_uni_m, eth_wm, bsc_uni_m, bsc_wm

from bot.db_client import db
from web3.exceptions import ContractLogicError
from bot.uniswap_utils import uniswap_base, sushiswap_base, pancakeswap_base
import datetime
from bot.utils.ca_helpers import process_erc20_token, generate_message, fetch_token_info, to_check_sum
from database.ca_functions import add_coin_data, update_coin_data, get_coin, get_users_tracking_coin
from database.trade_functions import store_active_trade
from database.payment_functions import add_fee_payment
from database.honeypot_functions import update_hp_contract, get_hp_contract
from database.user_settings_functions import get_active_paid_users, get_user_settings_by_user
from database.user_functions import update_user_with_user
from database.wallet_functions import get_active_network_wallet
import telebot

TOKEN = BOT_TOKEN

bot = telebot.TeleBot(TOKEN)


class UniswapListener:
    def __init__(self, exchange: str):
        self.uniswap_utils = UniswapUtils(exchange=exchange)
        self.web3 = self.uniswap_utils.web3
        self.router_address = self.uniswap_utils.router_address
        self.factory_address = self.uniswap_utils.factory_address
        self.api_id = 20762819
        self.api_hash = '719b682813fb2d9ed9e5186e97ecab74'
        self.channel_id = ['https://t.me/uniswapinstant','https://t.me/pancakeswapinstant','https://t.me/iTokenEthereum']
        self.name = "Telegram listner"
        self.network = "ethereum" if "uni" in exchange else ("bsc" if "pancake" in exchange else "arbitrum")
        
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s [%(name)s] %(levelname)s: %(message)s"))
        self.logger.addHandler(handler)


        self.logger.info("Sniper V2 has started!")

    async def _get_token_name_and_symbol(self, contract_address):
        token_abi = self.uniswap_utils.erc20_abi
        token_contract = self.web3.eth.contract(address=contract_address, abi=token_abi)
        name = token_contract.functions.name().call()
        symbol = token_contract.functions.symbol().call()
        return name, symbol

    async def send_trade_alert(self, user_chat_id, network, transaction_hash, action, token_name, token_symbol, amount, native_symbol):
        scan_url = {
            "ethereum": "https://etherscan.io/tx/",
            "arbitrum": "https://arbiscan.io/tx/",
            "bsc": "https://bscscan.com/tx/"
        }

        emoji_map = {
            "buy": "🟢",
            "sell": "🔴"
        }

        message = f'''
                    ⚡️🎉 *Trade Blast Alert* 🎉⚡️

                    💥 *Action Just Taken:* {action.title()}
                    🪙 *Token:* {token_name}
                    ✨ *Ticker:* {token_symbol}
                    🌐 *On Network:* {network.title()}
                    💰 *For An Amount Of:* {amount} {native_symbol}
                    🚀 *See The Magic Here:* [{transaction_hash}]({scan_url[network.lower()]}{transaction_hash})

                    Stay tuned for more action! 🌟🔥
                    '''

        bot.send_message(chat_id=user_chat_id, text=message, parse_mode=None)

    async def send_trade_fail_alert(self, user_id, symbol, wallet, error_message):
        # Define emojis
        warning_emoji = "\u26A0"  # Warning sign emoji
        sad_face_emoji = "\uD83D\uDE1E"  # Disappointed face emoji

        # Build the error message
        error_message = f"{warning_emoji} Transaction failed! {sad_face_emoji}\n\nError: {str(error_message)}"
        safe_error_message = error_message.encode('utf-8', errors='replace').decode('utf-8')
        try:
            bot.send_message(chat_id=user_id, text=safe_error_message, parse_mode=None)
        except:
            pass

    async def send_alert(self, event, name, symbol, liquidity, native_symbol, pair):
        try:
            if liquidity > 1:
                message = f'''🚀🚀🚀 *Liquidity Added Event* 🚀🚀🚀

                🪙 *Coin Name:* {name}
                🔤 *Symbol:* {symbol}
                💧 *Liquidity Amount:* {liquidity} {native_symbol}
                📄 *Pair Contract Address:* [{pair}](https://{"etherscan.io" if "uni" in self.name else "arbiscan.io"}/address/{pair})
                🔄 *Exchange:* {self.name.title().replace('_'," ")}
                🌐 *Network:* {"Ethereum" if "uni" in self.name else "Arbitrum"}

                💰💰💰 Happy Trading! 💰💰💰'''
                bot.send_message(chat_id=GROUP_CHAT_ID, text=message, parse_mode="MarkDown")
        except Exception as e:
            self.logger.error(f"Pair created event: {event} | {e}")

    async def _pair_created_callback(self, event):
        event = dict(event)
        name = event.get('name')
        quote = "WETH" if "ethereum" in event['network'] else "WBNB"
        symbol = event.get('base_token') if (event.get('base_token')!=quote) else event.get('quote_token')
        
        native_symbol = event.get('quote_token') if (event.get('quote_token') and event.get('quote_token')==quote) else event.get('base_token')
        if symbol!=native_symbol:
            if symbol=="WBNB" or symbol=="WETH":
                symbol,native_symbol=native_symbol,symbol
        liquidity = event.get('quote_token_liquidity') if event.get('quote_token')==quote else event.get('base_token_liquidity')
        if not liquidity:
            return
        if float(liquidity)==0:
            return
        contract_address = event.get('contract_address')
        tracking_users = await get_users_tracking_coin(contract_address,db)
        if contract_address:
            ca = to_check_sum(contract_address)
            coin = await get_coin(ca,db)
            if coin:
                data = fetch_token_info(ca)
                coin.price = data['price']
                coin.price_usd = data['price_usd']
                coin.liquidity = data['liquidity']
            else:
                data = process_erc20_token(ca, network="")
                coin = await add_coin_data(data, db)
        if contract_address:
            name = coin.name
            symbol = coin.symbol
            native_symbol = coin.quote_symbol
            block_number = uniswap_base.web3.eth.get_block_number()
            self.logger.info(f"Found a new pair: {event['network']} {name} | {symbol} | {liquidity}")
            hp_status = await get_hp_contract(contract_address, db)
            users = await get_active_paid_users(db)

            async def buy_for_user(user, target_block, network):
                user_setting = await get_user_settings_by_user(user, network, db)
                user_wallet = await get_active_network_wallet(user, network, db)
                if hp_status:
                    if (hp_status.hp or hp_status.high_tax or coin.is_honeypot) and user_setting.hp_toggle:
                        return
                try_count = 0
                while self.web3.eth.block_number < target_block:
                    await asyncio.sleep(2)
                
                if liquidity > user_setting.min_liquidity:
                    dex = None
                    if network == "ethereum":
                        dex = eth_uni_m
                        fee = 0.0035
                    elif network == "bsc":
                        dex = bsc_uni_m
                        fee = 0.035
                    else:
                        pass
                    if dex:
                        # for w in user.wallets:
                        #     print(w.network)
                        wallet = user_wallet
                        if wallet:
                            dex.address = wallet.wallet_address
                            dex.private_key = eth_wm.decrypt_seed(wallet.wallet_encrypted_seed)
                            
                            balance = dex.get_eth_balance()
                            qty = eth_wm.web3.to_wei(user_setting.amount_per_snipe, 'ether')
                            user.cumulative_fee = user.cumulative_fee if user.cumulative_fee else 0
                            # fee_due = eth_wm.web3.to_wei(fee, 'ether')
                            fee_due = 0
                            if network == "ethereum":
                                token_in = ETH_ADDRESS
                                path_in = WETH_ADDRESS
                                to = random.choice(ETH_FEE_WALLET) 
                            elif network == "bsc":
                                token_in = ETH_ADDRESS
                                path_in = WBNB_ADDRESS
                                to = BSC_FEE_WALLET
                            else:
                                token_in = WETH_ADDRESS_ARB
                                path_in = WETH_ADDRESS_ARB
                                to = ARB_FEE_WALLET
                            if "ethereum" in network.lower():
                                own_dex = uniswap_base
                                dex_name = "uniswap_v2"
                            elif "bsc" in network.lower():
                                own_dex = pancakeswap_base
                                dex_name = "pancakeswap_v2"
                            else:
                                own_dex = sushiswap_base
                            own_dex.wallet = dex.address
                            own_dex.private_key = dex.private_key
                            own_dex.web3 = dex.w3
                            if balance > qty + (fee_due * 1.3):
                                dex.default_slippage = float(user_setting.slippage) / 100
                                while try_count < 2:
                                    try:
                                        try:
                                            out_qty = dex.get_price_input(path_in,contract_address,qty)
                                            min_out_amount =  int((1-user_setting.slippage * 0.01) * out_qty)
                                            
                                            status, hsah = own_dex.swap_v2_eth_in(qty,min_out_amount,[path_in,contract_address],to=own_dex.wallet,deadline_seconds=30, gas_delta=user_setting.max_gas_price)
                                            if status:
                                                tx_hash = hsah
                                            else:
                                                self.logger.error(f"{self.name} Swap returned False")
                                                await self.send_trade_fail_alert(user.chat_id, symbol,own_dex.wallet, error_message=f"Snipe event failed for {symbol} | {self.name.split('_')[0]} due to error: {hsah}")
                                                return
                                            
                                        except ContractLogicError as e:
                                            error_message = e
                                            self.logger.error(f"Error while making the trade: {contract_address} {e}")
                                            # await self.send_trade_fail_alert(user.chat_id,symbol,wallet.wallet_address,error_message)
                                            return
                                        
                                        # user_id: int, token_address: str, token_in_address: str, tx_hash: str, trade_type: str, amount: float, token_qty, db
                                        
                                        price_in = get_pair_price(contract_address, token_in, dex=dex_name)
                                        balance = self.web3.from_wei(own_dex.get_token_balance(contract_address),'ether')
                                        user.cumulative_fee = user.cumulative_fee + user_setting.amount_per_snipe * PER_TX_FEE if user.cumulative_fee else user_setting.amount_per_snipe * PER_TX_FEE 
                                        # if True and user.id!=10:
                                            
                                            # status, hash = own_dex.transfer_native_token(to=to,amount=fee,priority_fee=5)
                                            # user.cumulative_fee = 0
                                            # fee_data = {}
                                            # fee_data['wallet_address']=own_dex.wallet
                                            # fee_data['network']=network.lower()
                                            # fee_data['amount']=fee
                                            # fee_data['tx_hash']=hash
                                            # fee_data['timestamp']=datetime.datetime.now()
                                            # await add_fee_payment(user.chat_id, fee_data, db)
                                            



                                        await update_user_with_user(user, db)
                                        
                                        await store_active_trade(user.id, network, contract_address, token_in, tx_hash, 'buy', qty, name, symbol, dex_name.replace("_",""), price_in, balance, db)
                                        await self.send_trade_alert(user.chat_id, network, tx_hash, 'buy', name, symbol, user_setting.amount_per_snipe, native_symbol)
                                        break
                                    except Exception as e:
                                        self.logger.error(f"Error making trade: {e}\n{user.id} | {dex.address} | {symbol}")
                                        try_count += 1
                                        dex.default_slippage = 1
                                        
                                        if try_count == 2 or "insufficient funds for gas * price + value" in str(e):
                                            self.logger.error("Reached maximum retry attempts for make_trade.")
                                            error_message = e
                                            await self.send_trade_fail_alert(user.chat_id,symbol,wallet.wallet_address,error_message)
                                        else:
                                            await asyncio.sleep(1)

                            elif False:
                                if balance<fee_due:
                                    amount = own_dex.web3.from_wei(balance,'ether') 
                                else:
                                    amount = user.cumulative_fee
                                status, hash = own_dex.transfer_native_token(to=to,amount=amount,priority_fee=5)
                                user.cumulative_fee = user.cumulative_fee - amount
                                fee_data = {}
                                fee_data['wallet_address']=own_dex.wallet
                                fee_data['network']=network.lower()
                                fee_data['amount']=amount
                                fee_data['tx_hash']=hash
                                fee_data['timestamp']=datetime.datetime.now()
                                await add_fee_payment(user.chat_id, fee_data, db)
        
            tasks = []
            for user in users:
                user_setting = await get_user_settings_by_user(user, event['network'], db)

                if user_setting:
                    if user_setting.auto_buy or user.id in tracking_users:
                        tasks.append(buy_for_user(user, block_number + user_setting.blocks_to_wait, event['network']))
            await asyncio.gather(*tasks)

    def parse_token_message(self, message):
        parsed_data = {}
        parsed_data['network'] = "ethereum"
        name_match = re.search(r'\*\*Name:\*\* (.+)', message)
        if name_match:
            parsed_data['name'] = name_match.group(1)
        
        total_supply_match = re.search(r'\*\*Total Supply:\*\* (.+)', message)
        if total_supply_match:
            parsed_data['total_supply'] = int(total_supply_match.group(1))
        
        contract_address_match = re.search(r'\*\*🦄 Uniswap:\*\* \[(.+)\]', message)
        if contract_address_match:
            parsed_data['contract_address'] = contract_address_match.group(1)
        
        base_token_liquidity_match = re.search(r'\*\*💎 (.+) liquidity:\*\* (.+) \1', message)
        if base_token_liquidity_match:
            parsed_data['base_token'] = base_token_liquidity_match.group(1)
            parsed_data['base_token_liquidity'] = int(base_token_liquidity_match.group(2))
        
        quote_token_liquidity_match = re.search(r'\*\*🍿 (.+) liquidity:\*\* (.+) \1', message)
        if quote_token_liquidity_match:
            parsed_data['quote_token'] = quote_token_liquidity_match.group(1)
            parsed_data['quote_token_liquidity'] = int(quote_token_liquidity_match.group(2))
    
        return parsed_data


    def parse_ps_message(self, message):
    
        parsed_data = {}
        parsed_data['network'] = "bsc"
        
        name_match = re.search(r'Name: (.+)', message)
        if name_match:
            parsed_data['name'] = name_match.group(1)
            
        symbol_match = re.search(r'New Pair found: (\w+)/(.+) ', message)
        if symbol_match:
            parsed_data['quote_token'] = symbol_match.group(1)
            parsed_data['base_token_symbol'] = symbol_match.group(2)
            
        total_supply_match = re.search(r'Total Supply: ([\d,]+)', message)
        if total_supply_match:
            parsed_data['total_supply'] = int(total_supply_match.group(1).replace(",", ""))
        contract_address_match = re.search(r'\((https://pancakeswap.info/token/|https://bscscan.com/token/)(0x[a-fA-F0-9]{40})\)', message)


        if contract_address_match:
            parsed_data['contract_address'] = contract_address_match.group(2)
            
        quote_token_liquidity_match = re.search(r'💎 (\w+) liquidity: ([\d\.]+)', message)
        if quote_token_liquidity_match:
            parsed_data['quote_token_liquidity'] = float(quote_token_liquidity_match.group(2))
            
        base_token_liquidity_match = re.search(r'🍿 (.+) liquidity: ([\d,]+)', message)
        if base_token_liquidity_match:
            parsed_data['base_token_liquidity'] = int(base_token_liquidity_match.group(2).replace(",", ""))



        return parsed_data

    def scan_contract(self, message):
        # split the message into lines
        lines = message.split('\n')

        # find the line that starts with 'CA: '
        contract_address_line = next((line for line in lines if line.startswith('CA: ')), None)
        if contract_address_line is not None:
            # split the line into two parts at 'CA: ', and take the second part as the contract address
            contract_address = contract_address_line.split('CA: ')[1]
        else:
            contract_address = None

        # find the line that starts with 'Scan: '
        scan_line = next((line for line in lines if line.startswith('Scan: ')), None)
        if scan_line is not None:
            # split the line into two parts at 'Scan: ', and take the second part as the scan result
            scan_result = scan_line.split('Scan: ')[1]
        else:
            scan_result = None

        return contract_address, scan_result

    async def start_listening(self):
        # Create a new Telegram client
        client = TelegramClient('anon', self.api_id, self.api_hash)

        # Connect to the client
        await client.start()

        # Listen for messages in the channel
        @client.on(events.NewMessage(chats=self.channel_id))
        async def new_message_listener(event):
            # Get the message text
            
            

            message = event.message.text
            
            if "scan" in message.lower() and "ca:" in message.lower():
                ca, status = self.scan_contract(message.replace("**","").replace('[','').replace(']','').replace('`','').strip())
                # self.logger.info(f"CA: {ca} | Status: {status}")
                if "honeypot" in status.lower() or "honeypot" in message.lower():
                    hp = True
                else:
                    hp = False
                if "tax" in status.lower() or "tax" in message.lower():
                    tax = True
                else:
                    tax = False
                data = {}
                data['ca'] = ca
                data['hp'] = hp
                data['high_tax'] = tax
                await update_hp_contract(data,db)
                
                return
            # Parse the message
            if "pancakeswap" in message.lower():
                parsed_data = self.parse_ps_message(message.replace("**","").replace('[','').replace(']','').strip())
                # self.logger.info(parsed_data)
            else:
                parsed_data = self.parse_token_message(message)

            # Pass the parsed data to the pair created event
            asyncio.create_task(self._pair_created_callback(parsed_data))

        # Run the client until it's disconnected
        await client.run_until_disconnected()





