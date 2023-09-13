from web3 import Web3, HTTPProvider
# from bot.utils.config import *
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
def check_and_replicate_trades():
    latest_block = w3.eth.block_number
    last_checked_block = latest_block

    while True:
        # Get new blocks since the last checked block
        latest_block = w3.eth.block_number
        if latest_block > last_checked_block:
            for block_number in range(last_checked_block + 1, latest_block + 1):
                print(block_number)
                if block_number: 
                    block = w3.eth.get_block(block_number, full_transactions=True)
                    for tx in block.transactions:
                        # print('From : ', tx['from'])
                        # print('To : ', tx['to'])
                        if 'input' in tx and (
                            tx['input'].startswith(swapETHForExactTokens) or
                            tx['input'].startswith(swapExactTokensForETHSupportingFeeOnTransferTokens) or
                            tx['input'].startswith(swapExactETHForTokensSupportingFeeOnTransferTokens) or
                            tx['input'].startswith(swapExactTokensForETH) or
                            tx['input'].startswith(swapExactETHForTokens)
                            ):
                            # Identifying trades based on specific criteria (e.g., function calls or contract interactions)
                            # Checking if the transaction interacts with a router contract of uniswap v2.
                            # Inspecting the transaction data and using ABI for decoding.
                            # If a trade condition is met, replicating the trade.
                            # Note: This is a highly inplemented as per our requirement example and actual trade conditions can be complex.
                            tx_input = tx['input']
                            # os.system('cls')
                            # print('Detected input --- ',tx_input)
                            decoded_input = router_contract.decode_function_input(tx['input'])
                            # print('Decoded input tx --- ',decoded_input)
                            decoded_args = decoded_input[1]
                            decoded_func = decoded_input[0]
                            
                            class_name = decoded_func.__class__.__name__
                            print("function name: ", class_name)
                            
                            for key, value in decoded_args.items():
                                print(f"{key} : {value}")

            last_checked_block = latest_block
            time.sleep(5)  # Check for new blocks every minute (adjust as needed)

# Define your trade condition logic here
def is_trade(tx):
    # Example: Check if the transaction interacts with a specific contract
    # You may need to inspect tx['input'] or use ABI to decode.
    return True

# Replicate a trade
def replicate_trade(tx):
    # Implement the logic to replicate the trade here.
    # You'll need to send a transaction from the follower address to replicate the trade.
    # Use the private key for signing the transaction.
    # Make sure to handle gas fees and error handling.
    pass

if __name__ == "__main__":
    check_and_replicate_trades()
