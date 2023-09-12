import asyncio
import logging
from web3 import Web3
from web3.types import FilterParams
from bot.uniswap_utils import UniswapUtils
from database.user_settings_functions import get_active_users_with_settings
from bot.utils.config import ETH_INFURA_URL, BSC_URL, ARB_INFURA_URL, GROUP_CHAT_ID, WETH_ADDRESS
from bot.app import bot

from bot.utils.wallet_methods import eth_uni_m, eth_uni_mv3, arb_uni_m, eth_wm
from database.trade_functions import store_active_trade
from bot.db_client import db
# from database import add_coin, get_coin_by_address, get_users_with_active_subscriptions_and_auto_buy

class SniperV2:
    def __init__(self, exchange: str):
        self.uniswap_utils = UniswapUtils(exchange=exchange)
        self.web3 = self.uniswap_utils.web3
        self.router_address = self.uniswap_utils.router_address
        self.factory_address = self.uniswap_utils.factory_address
        
        self.name = exchange
        if "uni" in exchange:
            network = "ethereum"
        elif "pancake" in exchange:
            network = "bsc"
        else:
            network = "arbitrum"
        self.network = network
        #def __init__(self, provider_url: str, address: str, private_key: str = None, exchange: str = "uniswap_v2", wallet_address=None):
        # Set up logging
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s [%(name)s] %(levelname)s: %(message)s"))
        self.logger.addHandler(handler)
        self.logger.info("Sniper V2 has started!")

    async def _get_token_name_and_symbol(self, contract_address):
        token_abi = self.uniswap_utils.erc20_abi  # Replace this with the token contract ABI
        token_contract = self.web3.eth.contract(address=contract_address, abi=token_abi)
        name = token_contract.functions.name().call()
        symbol = token_contract.functions.symbol().call()
        return name, symbol


    async def send_alert(self, event, name, symbol, liquidity, native_symbol, pair):
        try:
            if liquidity>1:
                    message = f'''🚀🚀🚀 *Liquidity Added Event* 🚀🚀🚀

    🪙 *Coin Name:* {name}
    🔤 *Symbol:* {symbol}
    💧 *Liquidity Amount:* {liquidity} {native_symbol}
    📄 *Pair Contract Address:* [{pair}](https://{"etherscan.io" if "uni" in self.name else "arbiscan.io"}/address/{pair})
    🔄 *Exchange:* {self.name.title().replace('_'," ")}
    🌐 *Network:* {"Ethereum" if "uni" in self.name else "BSC"}

    💰💰💰 Happy Trading! 💰💰💰'''
            await bot.send_message(chat_id=GROUP_CHAT_ID, text=message, parse_mode="MarkDown")
        except Exception as e:
            self.logger.error(f"Pair created event: {event} | {e}")

    async def _pair_created_callback(self, event):
        event = dict(event)
        # self.logger.info(event)
        token0, block_number = event["args"]["token0"], event["blockNumber"]
        token1, pair = event["args"]["token1"], event["args"]["pair"]
        if token0.lower()==WETH_ADDRESS.lower():
            contract_address = eth_wm.web3.to_checksum_address(token1) 
        else:
            contract_address = eth_wm.web3.to_checksum_address(token0)
        try:
            tx_hash = event['transactionHash'].hex()
        except:
            tx_hash = event['transactionHash']

        try:
            transaction = self.web3.eth.get_transaction(tx_hash)
            value = self.web3.from_wei(transaction['value'], 'ether')
            # self.logger.info(f"Pair Created Tx:\n {transaction}")
        except:
            value = -1
            pass
        liquidity = value
        try:
            name, symbol = await self._get_token_name_and_symbol(token0)
            if symbol=="WETH" or symbol=="WBNB":
                native_symbol = symbol
                name, symbol = await self._get_token_name_and_symbol(token1)
            else:
                _, native_symbol = await self._get_token_name_and_symbol(token1)

            self.logger.info(f"Pair ({name} | {symbol} | {liquidity}) created event")
            
            await self.send_alert(event, name, symbol, liquidity, native_symbol, pair)
        except:
            pass
        # if not await get_coin_by_address(contract_address):
        #     await add_coin(contract_address, name, symbol)

        users = await get_active_users_with_settings(self.network, db)

        async def buy_for_user(user, target_block):
            while self.web3.eth.block_number < target_block:
                await asyncio.sleep(2)
            if liquidity>user.settings.min_liquidity:
                dex = None
                if self.network == "ethereum":
                    if "v2" in self.name:
                        dex = eth_uni_m
                    else:
                        dex = eth_uni_mv3
                elif self.network == "arbitrum":
                    dex = arb_uni_m
                else:
                    pass
                if dex:
                    dex.address = user.wallets.wallet_address
                    dex.private_key = eth_wm.decrypt_seed(user.wallets.wallet_encrypted_seed)
                    balance = dex.get_eth_balance()
                    qty = eth_wm.web3.to_wei(user.settings.amount_per_snipe, 'ether')
                    if balance>qty:
                        dex.default_slippage = float(user.settings.slippage)/100
                        resp = dex.make_trade(WETH_ADDRESS,contract_address, qty)
                        tx_hash = resp.hex()
                        token_qty = dex.get_token_balance(contract_address)
                        await store_active_trade(user.id, contract_address, tx_hash, 'buy', qty, token_qty, db)
            return

        tasks = [buy_for_user(user, block_number + user.settings.blocks_to_wait) for user in users]
        await asyncio.gather(*tasks)



    async def start_listening(self):
        factory_contract = self.web3.eth.contract(address=self.factory_address, abi=self.uniswap_utils.uniswapv2_factory_abi)
        try:
            pair_created_filter = factory_contract.events.PairCreated.create_filter(fromBlock="latest")
        

            while True:
                events = pair_created_filter.get_new_entries()
                for event in events:
                    asyncio.create_task(self._pair_created_callback(event))

                await asyncio.sleep(1)  # Check for new events every 5 seconds
        except Exception as e:
            self.logger.error(f"Error: {e}")
