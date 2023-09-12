import asyncio
import logging
from web3 import Web3
from web3.types import FilterParams
from bot.uniswap_utils import UniswapUtils
from bot.utils.config import ADMIN_CHAT_ID
from bot.utils.config import ETH_INFURA_URL, BSC_URL, ARB_INFURA_URL, GROUP_CHAT_ID
# from database import add_coin, get_coin_by_address, get_users_with_active_subscriptions_and_auto_buy
from bot.app import bot
class SniperV3:
    def __init__(self, exchange: str):
        self.uniswap_utils = UniswapUtils(exchange=exchange)
        self.web3 = self.uniswap_utils.web3
        self.router_address = self.uniswap_utils.router_address
        self.factory_address = self.uniswap_utils.factory_address

        self.name = exchange

        # Set up logging
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s [%(name)s] %(levelname)s: %(message)s"))
        self.logger.addHandler(handler)
        self.logger.info("Sniper V3 has started!")
    
    async def _get_token_name_and_symbol(self, contract_address):

        token_abi = self.uniswap_utils.erc20_abi  # Replace this with the token contract ABI
        token_contract = self.web3.eth.contract(address=contract_address, abi=token_abi)
        name = token_contract.functions.name().call()
        symbol = token_contract.functions.symbol().call()
        return name, symbol

    async def _pool_created_callback(self, event):
        event = dict(event)
        # self.logger.info(event)
        token0, block_number = event["args"]["token0"], event["blockNumber"]
        token1, pair = event["args"]["token1"], event["args"]["pool"]

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
            if liquidity>1:
                message = f'''🚀🚀🚀 *Liquidity Added Event* 🚀🚀🚀

🪙 *Coin Name:* {name}
🔤 *Symbol:* {symbol}
💧 *Liquidity Amount:* {liquidity} {native_symbol}
📄 *Pair Contract Address:* [{pair}](https://etherscan.io/address/{pair})
🔄 *Exchange:* {self.name.title().replace('_'," ")}
🌐 *Network:* {"Ethereum" if "uni" in self.name else "BSC"}

💰💰💰 Happy Trading! 💰💰💰'''
                await bot.send_message(chat_id=GROUP_CHAT_ID, text=message, parse_mode="MarkDown")
        except Exception as e:
            self.logger.error(f"Pair created event: {event} | {e}")
        # contract_address, block_number = event["address"], event["blockNumber"]
        # name, symbol = await self._get_token_name_and_symbol(contract_address)

        # self.logger.info(f"Pair ({name} | {symbol}) created event: {event}")

        # if not await get_coin_by_address(contract_address):
        #     await add_coin(contract_address, name, symbol)

        # users = await get_users_with_active_subscriptions_and_auto_buy()

        # async def buy_for_user(user, target_block):
        #     while self.web3.eth.blockNumber < target_block:
        #         await asyncio.sleep(1)

        #     await self.uniswap_utils.swapv3(
        #         self.router_address,
        #         user.amount_in,
        #         user.amount_out_min,
        #         [self.web3.eth.defaultAccount, contract_address],
        #         user.address,
        #         user.deadline
        #     )

        # tasks = [buy_for_user(user, block_number + user.settings.blocks_to_wait) for user in users]
        # await asyncio.gather(*tasks)

    async def start_listening(self):
        factory_contract = self.web3.eth.contract(address=self.factory_address, abi=self.uniswap_utils.uniswapv3_factory_abi)
        pool_created_filter = factory_contract.events.PoolCreated.create_filter(fromBlock="latest")

        while True:
            try:
                events = pool_created_filter.get_new_entries()
                for event in events:
                    asyncio.create_task(self._pool_created_callback(event))

                await asyncio.sleep(5)  # Check for new events every 5 seconds
            except Exception as e:
                self.logger.error(f"Error: {e}")
