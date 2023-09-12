import asyncio
import logging
from web3 import Web3
from bot.uniswap_utils import UniswapUtils 
from database.user_settings_functions import get_active_paid_users, get_user_settings_by_user
from database.wallet_functions import get_active_network_wallet
from bot.utils.config import GROUP_CHAT_ID, WETH_ADDRESS, WETH_ADDRESS_ARB, WBNB_ADDRESS, ETH_ADDRESS, ADMIN_CHAT_ID
from bot.utils.config import PER_TX_FEE, FEE_CUTOFF, ETH_FEE_WALLET, BSC_FEE_WALLET, ARB_FEE_WALLET
from bot.utils.get_trade_stats  import get_pair_price
from bot.app import bot
from bot.utils.wallet_methods import eth_uni_m, eth_uni_mv3, arb_uni_m, eth_wm
from database.trade_functions import store_active_trade
from bot.db_client import db
from web3.exceptions import ContractLogicError
from bot.uniswap_utils import uniswap_base, sushiswap_base
from database.payment_functions import add_fee_payment
from database.user_functions import update_user_with_user
import datetime
from bot.utils.ca_helpers import process_erc20_token, generate_message, fetch_token_info, to_check_sum
from database.ca_functions import add_coin_data, update_coin_data, get_coin

class SniperV2:
    def __init__(self, exchange: str):
        self.uniswap_utils = UniswapUtils(exchange=exchange)
        self.web3 = self.uniswap_utils.web3
        self.router_address = self.uniswap_utils.router_address
        self.factory_address = self.uniswap_utils.factory_address

        self.name = exchange
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
    {emoji_map[action.lower()]} *Trade Alert*

    🎯 *Action:* {action.title()}
    🪙 *Token Name:* {token_name}
    🔤 *Symbol:* {token_symbol}
    🌐 *Network:* {network.title()}
    💰 *Amount:* {amount} {native_symbol}
    🔗 *Transaction:* [{transaction_hash}]({scan_url[network.lower()]}{transaction_hash})

    🚀 Happy Trading! 🚀
    '''

        await bot.send_message(chat_id=user_chat_id, text=message, parse_mode=None)

    async def send_trade_fail_alert(self, user_id, symbol, wallet, error_message):
        # Define emojis
        warning_emoji = "\u26A0"  # Warning sign emoji
        sad_face_emoji = "\uD83D\uDE1E"  # Disappointed face emoji

        # Build the error message
        error_message = f"{warning_emoji} Transaction failed! {sad_face_emoji}\n\nError: {str(error_message)}"
        safe_error_message = error_message.encode('utf-8', errors='replace').decode('utf-8')
        await bot.send_message(chat_id=user_id, text=safe_error_message, parse_mode=None)

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
                await bot.send_message(chat_id=GROUP_CHAT_ID, text=message, parse_mode="MarkDown")
        except Exception as e:
            self.logger.error(f"Pair created event: {event} | {e}")

    async def _pair_created_callback(self, event):
        event = dict(event)
        token0, block_number = event["args"]["token0"], event["blockNumber"]
        token1, pair = event["args"]["token1"], event["args"]["pair"]
        contract_address = eth_wm.web3.to_checksum_address(token1 if (token0.lower() == WETH_ADDRESS.lower() or token0.lower() == WETH_ADDRESS_ARB.lower()) else token0)
        tx_hash = event['transactionHash'].hex() if hasattr(event['transactionHash'], 'hex') else event['transactionHash']

        try:
            transaction = self.web3.eth.get_transaction(tx_hash)
            value = self.web3.from_wei(transaction['value'], 'ether')
        except:
            value = -1

        liquidity = value
        if float(liquidity)==0:
            return
        ca = to_check_sum(contract_address)
        coin = await get_coin(ca,db)
        if coin:
            data = fetch_token_info(ca)
            coin.price = data['price']
            coin.price_usd = data['price_usd']
            coin.liquidity = data['liquidity']
        else:
            data = process_erc20_token(ca, network="arbitrum")
            coin = await add_coin_data(data, db)
        try:
            name, symbol = coin.name, coin.symbol
            native_symbol = coin.quote_symbol
            if symbol == "WETH" or symbol == "WBNB":
                
                name, symbol = await self._get_token_name_and_symbol(token1)
            else:
                _, native_symbol = await self._get_token_name_and_symbol(token1)

            # await self.send_alert(event, name, symbol, liquidity, native_symbol, pair)
        except:
            pass
        self.logger.info(f"Found a new pair: {name} | {symbol} | {liquidity}")
        users = await get_active_paid_users(db)

        async def buy_for_user(user, target_block):
            user_setting = await get_user_settings_by_user(user, self.network, db)
            user_wallet = await get_active_network_wallet(user, self.network, db)

            try_count = 0
            while self.web3.eth.block_number < target_block:
                await asyncio.sleep(2)
            if liquidity > user_setting.min_liquidity:
                dex = None
                if self.network == "ethereum":
                    dex = eth_uni_m if "v2" in self.name else eth_uni_mv3
                elif self.network == "arbitrum":
                    dex = arb_uni_m
                else:
                    pass
                if dex:
                    # for w in user.wallets:
                    #     print(w.network)

                    wallet = user_wallet
                    if wallet:
                        network = wallet.network
                        dex.address = wallet.wallet_address
                        dex.private_key = eth_wm.decrypt_seed(wallet.wallet_encrypted_seed)
                        user.cumulative_fee = user.cumulative_fee if user.cumulative_fee else 0
                        balance = dex.get_eth_balance()
                        qty = eth_wm.web3.to_wei(user_setting.amount_per_snipe, 'ether')
                        fee_due = eth_wm.web3.to_wei(0.01, 'ether')
                        if network == "ethereum":
                            token_in = ETH_ADDRESS
                            path_in = WETH_ADDRESS
                            to = ETH_FEE_WALLET
                        elif network == "bsc":
                            token_in = ETH_ADDRESS
                            path_in = WBNB_ADDRESS
                            to = BSC_FEE_WALLET
                        else:
                            token_in = WETH_ADDRESS_ARB
                            path_in = WETH_ADDRESS_ARB
                            to = ARB_FEE_WALLET
                        if "uni" in self.name.lower():
                            own_dex = uniswap_base
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
                                        # resp = dex.make_trade(token_in, contract_address, qty)
                                        # tx_hash = resp.hex()
                                    except ContractLogicError as e:
                                        error_message = e
                                        self.logger.error(f"Error while making the trade: {contract_address} {e}")
                                        # await self.send_trade_fail_alert(user.chat_id,symbol,wallet.wallet_address,error_message)
                                        return
                                    # tx_hash = "0x"
                                    # user_id: int, token_address: str, token_in_address: str, tx_hash: str, trade_type: str, amount: float, token_qty, db
                                    price_in = get_pair_price(contract_address, token_in, dex=self.name)
                                    balance = self.web3.from_wei(own_dex.get_token_balance(contract_address),'ether')
                                    user.cumulative_fee = user.cumulative_fee + user_setting.amount_per_snipe * PER_TX_FEE if user.cumulative_fee else user_setting.amount_per_snipe * PER_TX_FEE 
                                    if True:
                                        
                                        status, hash = own_dex.transfer_native_token(to=to,amount=0.01,priority_fee=5)
                                        user.cumulative_fee = 0
                                        fee_data = {}
                                        fee_data['wallet_address']=own_dex.wallet
                                        fee_data['network']=network.lower()
                                        fee_data['amount']=0.01
                                        fee_data['tx_hash']=hash
                                        fee_data['timestamp']=datetime.datetime.now()
                                        await add_fee_payment(user.chat_id, fee_data, db)
                                        



                                    await update_user_with_user(user, db)
                                    await store_active_trade(user.id, self.network, contract_address, token_in, tx_hash, 'buy', qty, name, symbol, self.name.title().replace("_",""), price_in, balance, db)
                                    await self.send_trade_alert(user.chat_id, self.network, tx_hash, 'buy', name, symbol, user_setting.amount_per_snipe, native_symbol)
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
            user_setting = await get_user_settings_by_user(user, self.network, db)

            if user_setting:
                
                tasks.append(buy_for_user(user, block_number + user_setting.blocks_to_wait))
        await asyncio.gather(*tasks)

    async def start_listening(self):
        factory_contract = self.web3.eth.contract(address=self.factory_address, abi=self.uniswap_utils.uniswapv2_factory_abi)
        try:
            pair_created_filter = factory_contract.events.PairCreated.create_filter(fromBlock="latest")

            while True:
                events = pair_created_filter.get_new_entries()
                for event in events:
                    asyncio.create_task(self._pair_created_callback(event))

                await asyncio.sleep(1)
        except Exception as e:
            self.logger.error(f"Error: {e}")

