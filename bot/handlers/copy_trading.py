from web3 import Web3, HTTPProvider
from database.user_settings_functions import get_active_paid_users, get_user_settings_by_user
from database.wallet_functions import get_active_network_wallet
from database.copytradingaddress import getAddresses
from database.user_functions import get_user_by_id
from bot.utils.ca_helpers import process_erc20_token, generate_message, fetch_token_info, to_check_sum
from database.ca_functions import add_coin_data, update_coin_data, get_coin, get_users_tracking_coin
from database.trade_functions import store_active_trade
from bot.utils.uniswap_utils_copyTrade import uniswap_base
from bot.utils.wallet_methods import eth_uni_m, eth_wm
from web3.exceptions import ContractLogicError
import asyncio
# from bot.utils.config import *
from bot.db_client import db
import json
import os
import time

# Specify the path to your JSON file
json_file_path = 'bot/utils/uniswap_v2/uniswap_v2_router_abi.json'
UNISWAP_V2_ROUTER_ABI = ''
# Open the file and load the JSON data
with open(json_file_path, 'r') as json_file:
    UNISWAP_V2_ROUTER_ABI = json.load(json_file)

ETH_INFURA_URL = "https://eth-mainnet.g.alchemy.com/v2/1HZEUwVATL4Z6hzVdaeXWrJ6z6nLAAPu"
UNISWAP_V2_ROUTER_ADDRESS = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
dex = eth_uni_m
# Replace with your Ethereum node URL (e.g., Infura)
ethereum_node_url = ETH_INFURA_URL

# Initialize Web3 with an Ethereum node
w3 = Web3(HTTPProvider(ethereum_node_url))
router_contract = w3.eth.contract(address=UNISWAP_V2_ROUTER_ADDRESS, abi=UNISWAP_V2_ROUTER_ABI)
# router_contract.functions.swapExactTokensForTokens(0, 0, 0, 0, 0).selector.hex() 
# Replace these with the addresses of the leader and follower
leader_address = "0x28C6c06298d514Db089934071355E5743bf21d60"
follower_address = "0xFollowerAddress"

# Create a private key (for demonstration purposes, generate a private key securely in a real scenario)
private_key = "YOUR_PRIVATE_KEY"

# swapETHForExactTokens = '0xfb3bdb41'
# swapExactTokensForETHSupportingFeeOnTransferTokens = '0x791ac947'
# swapExactETHForTokensSupportingFeeOnTransferTokens = '0xb6f9de95'
# swapExactTokensForETH = '0x18cbafe5'
# swapExactETHForTokens = '0x7ff36ab5'

swapETHForExactTokens = b'\xfb\x3b\xdb\x41'
swapExactTokensForETHSupportingFeeOnTransferTokens = b'\x79\x1a\xc9\x47'
swapExactETHForTokensSupportingFeeOnTransferTokens = b'\xb6\xf9\xde\x95'
swapExactTokensForETH = b'\x18\xcb\xaf\xe5'
swapExactETHForTokens = b'\x7f\xf3\x6a\xb5'
# Function to check for and replicate trades
async def check_and_replicate_trades():
        addresses = await getAddresses()
        while True:
            # Get new blocks since the last checked block
            latest_block = w3.eth.block_number
            if latest_block > last_checked_block:
                for block_number in range(last_checked_block + 1, latest_block + 1):
                    print(block_number)
                    block = w3.eth.get_block(block_number, full_transactions=True)
                    for tx in block.transactions:
                        # Create a list of tasks
                        tasks = []
                        for address in addresses:
                            task = process_transaction(address, tx)
                            tasks.append(task)
                        # Run the tasks concurrently using asyncio
                        loop = asyncio.get_event_loop()
                        results = loop.run_until_complete(asyncio.gather(*tasks))

                        # Process the results if needed
                        for result in results:
                            if result is not None:
                                print(result)  # Handle errors or results as needed        

                last_checked_block = latest_block
                time.sleep(5)  # Check for new blocks every minute (adjust as needed)

# Define your trade condition logic here
async def process_transaction(address, tx):
    if 'to' in tx and tx['to'] == address:
        user = get_user_by_id(address.user_id)
        user_setting = await get_user_settings_by_user(user, 'ethereum', db)
        user_wallet = await get_active_network_wallet(user, 'ethereum', db)
    
        latest_block = w3.eth.block_number
        last_checked_block = latest_block
        wallet = user_wallet
        dex.address = wallet.wallet_address
        dex.private_key = eth_wm.decrypt_seed(wallet.wallet_encrypted_seed)
        own_dex = uniswap_base
        qty = eth_wm.web3.to_wei(user_setting.amount_per_snipe, 'ether')
        if 'input' in tx and (
            # tx['input'].startswith(swapETHForExactTokens) or
            # tx['input'].startswith(swapExactTokensForETHSupportingFeeOnTransferTokens) or
            tx['input'].startswith(swapExactETHForTokensSupportingFeeOnTransferTokens) or
            # tx['input'].startswith(swapExactTokensForETH) or
            tx['input'].startswith(swapExactETHForTokens)
            ):
            # Identifying trades based on specific criteria (e.g., function calls or contract interactions)
            # Checking if the transaction interacts with a router contract of uniswap v2.
            # Inspecting the transaction data and using ABI for decoding.
            # If a trade condition is met, replicating the trade.
            # Note: This is a highly inplemented as per our requirement example and actual trade conditions can be complex.
            decoded_input = router_contract.decode_function_input(tx['input'])
            decoded_args = decoded_input[1]
            decoded_func = decoded_input[0]
            
            class_name = decoded_func.__class__.__name__
            print("function name: ", class_name)
            path = decoded_args['path']
            for key, value in decoded_args:
                print(f'{key} : {value}')
            if class_name == 'swapExactETHForTokens':
                ca = to_check_sum(path[1])
                coin = await get_coin(ca,db)
                if coin:
                    data = fetch_token_info(ca)
                    coin.price = data['price']
                    coin.price_usd = data['price_usd']
                    coin.liquidity = data['liquidity']
                else:
                    data = process_erc20_token(ca, network="")
                    coin = await add_coin_data(data, db)
                out_qty = dex.get_price_input(path[0],path[1],qty)
                min_out_amount =  int((1-user_setting.slippage * 0.01) * out_qty) 
                try:    
                    status, hash = own_dex.swap_v2_eth_in(qty,min_out_amount,path,to=own_dex.wallet,deadline_seconds=30, gas_delta=user_setting.max_gas_price)
                    if status:
                        tx_hash = hash
                        await store_active_trade(user.id, 'ethereum', path[1], path[0], tx_hash, 'buy', qty, coin.name, coin.symbol, 'uniswapv2', price_in, price_in, db)
                    else:
                        error_message = f"Snipe event failed due to error: {hash}"
                        return error_message
                    # resp = dex.make_trade(token_in, contract_address, qty)
                    # tx_hash = resp.hex()
                except ContractLogicError as e:
                        error_message = e
                        print(f"Error while making the trade: {path[1]} {e}")
                        # await self.send_trade_fail_alert(user.chat_id,symbol,wallet.wallet_address,error_message)
                        return
            elif class_name == 'swapExactETHForTokensSupportingFeeOnTransferTokens':
                price_in = dex.get_price_input(path[0], path[1], qty)
                min_out_amount = int((1 - user_setting.sell_slippage * 0.01) * price_in)
                try:    
                    status, hash = own_dex.swap_v2_eth_in_withSupportingFee(qty,min_out_amount,path,to=own_dex.wallet,deadline_seconds=30, gas_delta=user_setting.max_gas_price)
                    if status:
                        tx_hash = hash
                        await store_active_trade(user.id, 'ethereum', path[1], path[0], tx_hash, 'buy', qty, coin.name, coin.symbol, 'uniswapv2', price_in, price_in, db)
                    else:
                        error_message = f"Snipe event failed due to error: {hash}"
                        return error_message
                    # resp = dex.make_trade(token_in, contract_address, qty)
                    # tx_hash = resp.hex()
                except ContractLogicError as e:
                        error_message = e
                        print(f"Error while making the trade: {path[1]} {e}")
                        # await self.send_trade_fail_alert(user.chat_id,symbol,wallet.wallet_address,error_message)
                        return


# Replicate a trade
def replicate_trade(tx):
    # Implement the logic to replicate the trade here.
    # You'll need to send a transaction from the follower address to replicate the trade.
    # Use the private key for signing the transaction.
    # Make sure to handle gas fees and error handling.
    pass

if __name__ == "__main__":
    check_and_replicate_trades()
