from bot.utils.wallet_methods import eth_test_wm, eth_uni_m, eth_uni_mv3, arb_uni_m, arb_wm
from database.models import ActiveTrades, Wallet, User
from database.trade_functions import set_trade_status_by_id
from database.user_settings_functions import get_user_settings_by_user, get_user_settings
from database.user_functions import get_user
from bot.db_client import db
from typing import List
import logging
from web3.exceptions import ContractLogicError
from bot.uniswap_utils import uniswap_base, sushiswap_base
from bot.utils.config import WETH_ADDRESS, ETH_ADDRESS, WETH_ADDRESS_ARB, WBNB_ADDRESS
from database.trade_functions import delete_trade
# from bot.app_client import bot


import asyncio


logger = logging.getLogger(__name__)
logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        )


# uniswap_base.calculate_v2_price()

def get_pair_price(token_in, token_out, dex):
    try:
        if "uni" in dex.lower():
            router = uniswap_base
        else:
            router = sushiswap_base
        # logger.info(f"Token In: {token_in} | Token Out: {token_out} | Dex: {dex}")
        # token_in_decimals = router.get_token(token_in).decimals
        # price = (router.get_price_input(token_in, token_out , 10**18))
        # out_price = (price/10**(token_in_decimals))
        if token_in==ETH_ADDRESS:
            if "uni" in dex.lower():
                token_in = WETH_ADDRESS
            else:
                token_in = WETH_ADDRESS_ARB
        out_price = router.calculate_v2_price(token_in, token_out)
        # logger.info(f"Token Price: {out_price}")
        return out_price
    except Exception as e:
        logger.error(f"Token Price: {e}")
        return 0
    

async def sell_trade(user: User, trade: ActiveTrades, wallet: Wallet):
    try:
        if trade.network == "ethereum":
            own_dex = uniswap_base
            own_dex.wallet = wallet.wallet_address
            dex = eth_uni_m
            dex_h = eth_test_wm
            token_out = WETH_ADDRESS
        else:
            own_dex = sushiswap_base
            own_dex.wallet = wallet.wallet_address
            dex = arb_uni_m
            dex_h = arb_wm
            token_out = WETH_ADDRESS_ARB
        balance = own_dex.get_token_balance(trade.token_address)

        if balance == 0:
            await delete_trade(trade, db)
            return False, "Balance is zero"
        price_in = dex.get_price_input(trade.token_address, token_out, balance)
        own_dex.wallet = wallet.wallet_address
        own_dex.private_key = dex_h.decrypt_seed(wallet.wallet_encrypted_seed)
        own_dex.web3 = dex.w3
        user_setting = await get_user_settings_by_user(user, trade.network, db)

        min_out_amount = int((1 - user_setting.sell_slippage * 0.01) * price_in)
        status, hsah = own_dex.swap_token_to_eth(balance, min_out_amount, [trade.token_address, token_out], own_dex.wallet, deadline_seconds=60, gas_delta=4)

        if status:
            tx_hash = hsah
            await set_trade_status_by_id(trade.id, db)
            return True, tx_hash
        else:
            logger.error(f"{trade.coin_dex} Swap returned False")
            return False, hsah
    except ContractLogicError as e:
        logger.error(f"Error in sell function: {e}")
        logger.error(f"Error in sell function: {balance} | {min_out_amount} | {trade.token_address} | {token_out} | {own_dex.wallet}")
        return False, str(e)
    except Exception as e:
        logger.error(f"Unexpected error in sell function: {e}")
        return False, str(e)


async def sell_all(user: User, trades: List[ActiveTrades], wallet):
    async def process_trade(trade):
        result = {'Symbol': trade.coin_symbol}
        try:
            status, resp = await sell_trade(user, trade, wallet)
            result['Status'] = status
            result['Response'] = resp
        except Exception as e:
            result['Status'] = False
            result['Response'] = str(e)
        return result

    # Run sell_trade concurrently for all trades and gather the results
    results = await asyncio.gather(*[process_trade(trade) for trade in trades])

    # Format the message with emojis and send it to the user's chat_id
    for result in results:
        if result['Status']:
            status_emoji = "✅"
        else:
            status_emoji = "❌"

        message = f"{status_emoji} Symbol: {result['Symbol']}\nResponse: {result['Response']}"

        
        chat_id = user.chat_id
        from bot.app import bot
        await bot.send_message(chat_id=chat_id, text=message)

    return results