from bot.wallet_manager import WalletManager
from bot.utils.config import ENCRYPTION_KEY, ETH_INFURA_URL, ARB_INFURA_URL, BSC_URL, ETH_TEST_URL

from uniswap import Uniswap


eth_uni_m = Uniswap(private_key=None,address=None,provider=ETH_INFURA_URL, version=2, use_estimate_gas=True, default_slippage=0.01)
bsc_uni_m = Uniswap(private_key=None,address=None,provider=BSC_URL, version=2, use_estimate_gas=True, default_slippage=0.01)
eth_uni_mv3 = Uniswap(private_key=None,address=None,provider=ETH_INFURA_URL, version=3, use_estimate_gas=True, default_slippage=0.01)
arb_uni_m = Uniswap(private_key=None,address=None,provider=ETH_INFURA_URL, version=2, use_estimate_gas=True, default_slippage=0.01)

eth_test_wm = WalletManager(network_url=ETH_TEST_URL, encryption_key=ENCRYPTION_KEY)


eth_wm = WalletManager(network_url=ETH_INFURA_URL, encryption_key=ENCRYPTION_KEY)
arb_wm = WalletManager(network_url=ARB_INFURA_URL, encryption_key=ENCRYPTION_KEY)
bsc_wm = WalletManager(network_url=BSC_URL, encryption_key=ENCRYPTION_KEY)

def get_uniswap_class(network):
    if network == "ethereum":
        return eth_uni_m
    elif network == "bsc":
        return bsc_uni_m
    else:
        return arb_uni_m


def send_wallet_info_message(wallets):
    if wallets:
        message = "🔐 *Your Active Wallet Details* 🔐\n\n"
    else:
        message = "🌟 *Wallet Central* 🌟\nLooks like you haven't set up any wallets yet. Time to create/connect one!\n"

    
    for wallet in wallets:
        name = wallet['name']
        unit = ""

        if "eth" in wallet['network'].lower():
            balance = eth_wm.get_balance(wallet['address'])
            unit = "ETH"
        elif "bsc" in wallet['network'].lower():
            balance = bsc_wm.get_balance(wallet['address'])
            unit = "BNB"
        else:
            balance = arb_wm.get_balance(wallet['address'])
            unit = "ETH"
        
        address = wallet['address']

        message += f"📔 *Wallet*: {name}\n"
        message += f"🪙 *Funds*: {balance} {unit}\n"
        message += f"🏠 *Address*: `{address}`\n"
        message += "------\n"
    
    return message
