from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware
import json, time

from bot.utils.config import UNISWAP_V2_FACTORY_ADDRESS, UNISWAP_V2_ROUTER_ADDRESS, UNISWAP_V3_FACTORY_ADDRESS, UNISWAP_V3_ROUTER_ADDRESS, ETH_INFURA_URL, HOLDING_TOKEN_ADDRESS, ARB_INFURA_URL, BSC_URL
from bot.utils.config import PANCAKESWAP_V2_FACTORY_ADDRESS, PANCAKESWAP_V2_ROUTER_ADDRESS, PANCAKESWAP_V3_FACTORY_ADDRESS, PANCAKESWAP_V3_ROUTER_ADDRESS, SUSHISWAP_FACTORY_ADDRESS, SUSHISWAP_ROUTER_ADDRESS
from bot.utils.config import WETH_ADDRESS, WETH_ADDRESS_ARB, WBNB_ADDRESS, ETH_FEE_WALLET, BSC_FEE_WALLET, ARB_FEE_WALLET
import logging



class UniswapUtils:
    
    def __init__(self, provider_url: str = None, address: str = "0xdAC17F958D2ee523a2206206994597C13D831ec7", private_key: str = None, exchange: str = "uniswap_v2", wallet_address=None):
        
        self.private_key = private_key
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(
                    level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
                )
        self.uniswapv2_router_abi = json.load(open("bot/utils/uniswap_v2/uniswap_v2_router_abi.json"))
        self.uniswapv3_router_abi = json.load(open("bot/utils/uniswap_v3/uniswap_v3_router_abi.json"))
        self.uniswapv2_factory_abi = json.load(open("bot/utils/uniswap_v2/uniswap_v2_factory_abi.json"))
        self.uniswapv3_factory_abi = json.load(open("bot/utils/uniswap_v3/uniswap_v3_factory_abi.json"))
        self.uniswapv3_nft_abi = json.load(open("bot/utils/uniswap_v3/uniswap_v3_nft_abi.json"))
        self.erc20_abi = json.load(open("bot/utils/erc20_abi.json"))
        self.uniswapv2_pair_abi = json.load(open("bot/utils/uniswap_v2/uniswap_v2_pair_abi.json"))
        self.wallet = wallet_address
        self.name = exchange
        if exchange=="uniswap_v2":
            self.web3 = Web3(Web3.HTTPProvider(ETH_INFURA_URL))
            self.web3.middleware_onion.inject(geth_poa_middleware, layer=0)
            self.factory_address = self.web3.to_checksum_address(UNISWAP_V2_FACTORY_ADDRESS)
            self.router_address = self.web3.to_checksum_address(UNISWAP_V2_ROUTER_ADDRESS)
            
        elif exchange=="uniswap_v3":
            self.web3 = Web3(Web3.HTTPProvider(ETH_INFURA_URL))
            self.web3.middleware_onion.inject(geth_poa_middleware, layer=0)
            self.factory_address = self.web3.to_checksum_address(UNISWAP_V3_FACTORY_ADDRESS)
            self.router_address = self.web3.to_checksum_address(UNISWAP_V3_ROUTER_ADDRESS)
        elif exchange=="sushiswap":
            self.web3 = Web3(Web3.HTTPProvider(ARB_INFURA_URL))
            self.web3.middleware_onion.inject(geth_poa_middleware, layer=0)
            self.factory_address = self.web3.to_checksum_address(SUSHISWAP_FACTORY_ADDRESS)
            self.router_address = self.web3.to_checksum_address(SUSHISWAP_ROUTER_ADDRESS)
        elif exchange=="pancakeswap_v2":
            self.web3 = Web3(Web3.HTTPProvider(BSC_URL))
            self.web3.middleware_onion.inject(geth_poa_middleware, layer=0)
            self.factory_address = self.web3.to_checksum_address(PANCAKESWAP_V2_FACTORY_ADDRESS)
            self.router_address = self.web3.to_checksum_address(PANCAKESWAP_V2_ROUTER_ADDRESS)
        elif exchange=="pancakeswap_v3":
            self.web3 = Web3(Web3.HTTPProvider(BSC_URL))
            self.web3.middleware_onion.inject(geth_poa_middleware, layer=0)
            self.factory_address = self.web3.to_checksum_address(PANCAKESWAP_V3_FACTORY_ADDRESS)
            self.router_address = self.web3.to_checksum_address(PANCAKESWAP_V3_ROUTER_ADDRESS)
        else:
            raise "Wrong exchange specified."
        self.address = self.web3.to_checksum_address(address) 

    def transfer_native_token(self, to: str, amount: int, priority_fee: int):
        amount = self.web3.to_wei(amount,'ether')
        nonce = self.web3.eth.get_transaction_count(self.wallet)
        gas_price = self.web3.eth.gas_price
        gas = 21000
        if priority_fee:
            gas_price = self.web3.from_wei(gas_price,'gwei') + int(priority_fee)
            gas_price = self.web3.to_wei(gas_price, 'gwei')
        try:
            while True:
                try:
                    transaction = {
                                    'to': to,
                                    'value': amount,
                                    'gas': gas,
                                    'gasPrice': gas_price,
                                    'chainId': self.web3.eth.chain_id,
                                    'nonce': nonce,
                                }

                    # Add priority fee (also called max priority fee per gas or tip) to gas price
                    transaction['gasPrice'] += priority_fee
                    signed_tx = self.web3.eth.account.sign_transaction(transaction, self.private_key)
                    tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
                    return True, tx_hash.hex()
                    # # Wait for the transaction to be mined and get the receipt
                    # tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
                    # if tx_receipt['status'] == 1:
                    #     return True, tx_hash.hex()
                    # else:
                    #     return False, tx_hash.hex()
                except Exception as e:
                    print(e)
                    if "nonce" in str(e) or "future" in str(e):
                        nonce+=1
                        continue
                    elif "underprice" in str(e):
                        priority_fee += 1
                        gas_price = self.web3.from_wei(gas_price,'gwei') + int(priority_fee)
                        gas_price = self.web3.to_wei(gas_price, 'gwei')
                    else:
                        return False, str(e)
            # Check if the transaction was successful (status == 1)
            
        except Exception as e:
            print(f"Error during the swap: {e}")
            return False, None

    def transfer_erc20_token(self, token_contract: str, to: str, amount: int):
        erc20_abi = self.erc20_abi
        contract = self.web3.eth.contract(address=token_contract, abi=erc20_abi)
        nonce = self.web3.eth.get_transaction_count(self.wallet)
        
        gas_price = self.web3.eth.gas_price
        # print(self.get_token_balance(token_contract))
            # Estimate gas instead of using a fixed value
            
        while True:
            try:
                gas = contract.functions.transfer(to, amount).estimate_gas({'from': self.wallet})
                data = contract.functions.transfer(to, amount).build_transaction({
                                                                                'from': self.wallet,
                                                                                'gas': gas,
                                                                                'gasPrice': gas_price,
                                                                                'nonce': nonce,
                                                                            })['data']

                transaction = {
                    'to': token_contract,
                    'value': 0,
                    'gas': gas,
                    'gasPrice': gas_price,
                    'nonce': nonce,
                    'chainId': self.web3.eth.chain_id,
                    'data': data,
                }

                signed_tx = self.web3.eth.account.sign_transaction(transaction, self.private_key)
            
                tx_hash =  self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
                tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
                if tx_receipt['status'] == 1:
                        return True, tx_hash.hex()
                else:
                    return False, tx_hash.hex()
            except Exception as e:
                print(e)
                if "nonce" in str(e) or "future" in str(e):
                    nonce+=1
                    continue
                elif "underprice" in str(e):
                    gas_price = int(gas_price*1.05)
                    continue
                # print(f"Address: {self.address} | Gas Price: {gas_price} | Burn Amount {amount}")
                return False, str(e)


    def approve(self, token_address, amount):
        token_address = self.web3.to_checksum_address(token_address)
        gas_price = self.web3.eth.gas_price
        gas = 300000  # Adjust gas limit as needed

        token_contract = self.web3.eth.contract(address=token_address, abi=self.erc20_abi)
        data = token_contract.encodeABI(fn_name='approve', args=[self.router_address,amount])
        # transaction_data = token_contract.functions.approve(self.router_address, amount).build_transaction({
        #     'from': self.wallet,
        #     'gas': gas,
        #     'gasPrice': gas_price,
        #     'nonce': self.web3.eth.get_transaction_count(self.wallet),
        # })
        transaction = {
            'to': token_address,
            'value': 0,
            'gas': gas,
            'gasPrice': gas_price,
            'nonce': self.web3.eth.get_transaction_count(self.wallet),
            'data': data,
        }

        signed_txn = self.web3.eth.account.sign_transaction(transaction, self.private_key)
        txn_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        resp = self.web3.eth.wait_for_transaction_receipt(txn_hash)
        
        return resp

    def swap_v2(self, amount_in: int, amount_out_min: int, path: list, to: str, deadline: int):
        router_address = self.router_address
        uniswap_v2_router_abi = self.uniswapv2_router_abi
        contract = self.web3.eth.contract(address=router_address, abi=uniswap_v2_router_abi)
        nonce = self.web3.eth.get_transaction_count(self.wallet)
        gas_price = self.web3.eth.gas_price
        gas = 300000  # Adjust gas limit as needed

        data = contract.encodeABI(fn_name='swapExactTokensForTokens', args=[amount_in, amount_out_min, path, to, deadline])

        

        try:
            while True:
                try:
                    transaction = {
                    'to': router_address,
                    'value': 0,
                    'gas': gas,
                    'gasPrice': gas_price,
                    'nonce': nonce,
                    'data': data,
                }
                    signed_tx = self.web3.eth.account.sign_transaction(transaction, self.private_key)
                    tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
                    tx_hash_hex = tx_hash.hex()  # Convert the transaction hash to its hexadecimal representation
                    tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
                    if tx_receipt['status'] == 1:
                        return True, tx_hash.hex()
                    else:
                        return False, tx_hash.hex()
                except Exception as e:
                        print(e)
                        if "nonce" in str(e) or "future" in str(e):
                            nonce+=1
                            continue
                        else:
                            return False, str(e)
            
        except Exception as e:
            print(f"Error during the swap: {e}")
            return False, None

    
    def swap_v2_eth_in(self, eth_amount: int, amount_out_min: int, path: list, to: str, deadline_seconds: int, gas_delta=None):
        router_address = self.router_address
        uniswap_v2_router_abi = self.uniswapv2_router_abi
        contract = self.web3.eth.contract(address=router_address, abi=uniswap_v2_router_abi)
        nonce = self.web3.eth.get_transaction_count(self.wallet)
        gas_price = self.web3.eth.gas_price
        
        deadline = int(time.time()) + deadline_seconds
        if gas_delta:
            gas_price = self.web3.from_wei(gas_price,'gwei') + int(gas_delta)
            gas_price = self.web3.to_wei(gas_price, 'gwei')
        # if self.name == "uniswap_v2":
        #     gas = 350000  # Adjust gas limit as needed
        # else:
        gas = contract.functions.swapExactETHForTokens(
            amount_out_min,
            path,
            to,
            deadline
        ).estimate_gas({"from": self.wallet, "value": eth_amount})
        gas = int(gas * 1.2)
        # Calculate the deadline timestamp
        data = contract.encodeABI(fn_name='swapExactETHForTokens', args=[amount_out_min, path, to, deadline])
        try:
            while True:
                try:
                    transaction = {
                    'to': router_address,
                    'value': eth_amount,  # Set the value to the amount of ETH you want to swap
                    'gas': gas,
                    'gasPrice': gas_price,
                    'nonce': nonce,
                    'chainId': self.web3.eth.chain_id,
                    'data': data,
                }
                    signed_tx = self.web3.eth.account.sign_transaction(transaction, self.private_key)
                    tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
                    tx_hash_hex = tx_hash.hex()  # Convert the transaction hash to its hexadecimal representation
                    self.logger.info(f"Hex of transaction is: {tx_hash_hex}")
                    return True, tx_hash_hex
                    # tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
                    # if tx_receipt['status'] == 1:
                    #     return True, tx_hash.hex()
                    # else:
                    #     return False, tx_hash.hex()
                    break
                except Exception as e:
                    if "nonce" in str(e) or "future" in str(e):
                        nonce+=1
                        continue
                    elif "underprice" in str(e):
                        gas_price = self.web3.from_wei(gas_price,'gwei') + 10
                        gas_price = self.web3.to_wei(gas_price, 'gwei')
                        continue
                    return False, str(e)
                
            
        except Exception as e:
            self.logger.error(f"Error during the swap: {e}")
            return False, None


    def swap_v2_eth_in_withSupportingFee(self, eth_amount: int, amount_out_min: int, path: list, to: str, deadline_seconds: int, gas_delta=None):
        router_address = self.router_address
        uniswap_v2_router_abi = self.uniswapv2_router_abi
        contract = self.web3.eth.contract(address=router_address, abi=uniswap_v2_router_abi)
        nonce = self.web3.eth.get_transaction_count(self.wallet)
        gas_price = self.web3.eth.gas_price
        
        deadline = int(time.time()) + deadline_seconds
        if gas_delta:
            gas_price = self.web3.from_wei(gas_price,'gwei') + int(gas_delta)
            gas_price = self.web3.to_wei(gas_price, 'gwei')
        # if self.name == "uniswap_v2":
        #     gas = 350000  # Adjust gas limit as needed
        # else:
        gas = contract.functions.swapExactETHForTokensSupportingFeeOnTransferTokens(
            amount_out_min,
            path,
            to,
            deadline
        ).estimate_gas({"from": self.wallet, "value": eth_amount})
        gas = int(gas * 1.2)
        # Calculate the deadline timestamp
        data = contract.encodeABI(fn_name='swapExactETHForTokensSupportingFeeOnTransferTokens', args=[amount_out_min, path, to, deadline])
        try:
            while True:
                try:
                    transaction = {
                    'to': router_address,
                    'value': eth_amount,  # Set the value to the amount of ETH you want to swap
                    'gas': gas,
                    'gasPrice': gas_price,
                    'nonce': nonce,
                    'chainId': self.web3.eth.chain_id,
                    'data': data,
                }
                    signed_tx = self.web3.eth.account.sign_transaction(transaction, self.private_key)
                    tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
                    tx_hash_hex = tx_hash.hex()  # Convert the transaction hash to its hexadecimal representation
                    self.logger.info(f"Hex of transaction is: {tx_hash_hex}")
                    return True, tx_hash_hex
                    # tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
                    # if tx_receipt['status'] == 1:
                    #     return True, tx_hash.hex()
                    # else:
                    #     return False, tx_hash.hex()
                    break
                except Exception as e:
                    if "nonce" in str(e) or "future" in str(e):
                        nonce+=1
                        continue
                    elif "underprice" in str(e):
                        gas_price = self.web3.from_wei(gas_price,'gwei') + 10
                        gas_price = self.web3.to_wei(gas_price, 'gwei')
                        continue
                    return False, str(e)
                
            
        except Exception as e:
            self.logger.error(f"Error during the swap: {e}")
            return False, None

    

    def swap_token_to_eth_old(self, token_amount: int, amount_out_min: int, path: list, to: str, deadline_seconds: int, gas_delta=None):
        router_address = self.router_address
        uniswap_v2_router_abi = self.uniswapv2_router_abi
        contract = self.web3.eth.contract(address=router_address, abi=uniswap_v2_router_abi)
        nonce = self.web3.eth.get_transaction_count(self.wallet)
        gas_price = self.web3.eth.gas_price
        deadline = int(time.time()) + deadline_seconds
        token_contract = self.web3.eth.contract(address=path[0], abi=self.erc20_abi)
        if gas_delta:
            gas_price = self.web3.from_wei(gas_price,'gwei') + int(gas_delta)
            gas_price = self.web3.to_wei(gas_price, 'gwei')
        
        # if self.name == "uniswap_v2":
        #     gas = 350000  # Adjust gas limit as needed
        # else:

        while True:
            try:
                txn = token_contract.functions.approve(router_address, token_amount).build_transaction({

                    
                    'chainId': self.web3.eth.chain_id,
                    'gas': 35000,
                    'gasPrice': gas_price,
                    'nonce': nonce,
                })
                signed_txn = self.web3.eth.account.sign_transaction(txn, private_key=self.private_key)
                tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
                tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
                
                if tx_receipt['status'] != 1:
                    return False, "Approval Tx Failed."
                else:
                    logging.info(f"Tx is approved")
                    break
            except ValueError as e:
                if "nonce" in str(e) or "replacement transaction underpriced" in str(e):
                    nonce += 1
                    continue
                self.logger.error(f"Error in approve: {e}")
                return False, str(e)

        nonce += 1

        data = contract.encodeABI(fn_name='swapExactTokensForETH', args=[token_amount, amount_out_min, path, to, deadline])
        transaction = {
            'to': router_address,
            'value': 0,
            'gas': 350000,
            'gasPrice': gas_price,
            'nonce': nonce,
            'data': data,
            'chainId': self.web3.eth.chain_id,
            'from':self.wallet
        }

        try:
            signed_tx = self.web3.eth.account.sign_transaction(transaction, self.private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_hash_hex = tx_hash.hex()
            tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            if tx_receipt['status'] == 1:
                return True, tx_hash_hex
            else:
                return False, tx_hash_hex
        except Exception as e:
            print(f"Error during the swap: {e}")
            return False, None


    def swap_token_to_eth(self, token_amount: int, amount_out_min: int, path: list, to: str, deadline_seconds: int, gas_delta=None):
        router_address = self.router_address
        uniswap_v2_router_abi = self.uniswapv2_router_abi
        contract = self.web3.eth.contract(address=router_address, abi=uniswap_v2_router_abi)
        nonce = self.web3.eth.get_transaction_count(self.wallet)
        gas_price = self.web3.eth.gas_price
        deadline = int(time.time()) + deadline_seconds
        token_contract = self.web3.eth.contract(address=path[0], abi=self.erc20_abi)
        if gas_delta:
            gas_price = self.web3.from_wei(gas_price,'gwei') + int(gas_delta)
            gas_price = self.web3.to_wei(gas_price, 'gwei')

        while True:
            try:
                txn = token_contract.functions.approve(router_address, token_amount).build_transaction({
                    'chainId': self.web3.eth.chain_id,
                    'gas': 35000,
                    'gasPrice': gas_price,
                    'nonce': nonce,
                })
                signed_txn = self.web3.eth.account.sign_transaction(txn, private_key=self.private_key)
                tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
                tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)

                if tx_receipt['status'] != 1:
                    return False, "Approval Tx Failed."
                else:
                    logging.info(f"Tx is approved")
                    break
            except ValueError as e:
                if "nonce" in str(e) or "replacement transaction underpriced" in str(e):
                    nonce += 1
                    continue
                self.logger.error(f"Error in approve: {e}")
                return False, str(e)

        nonce += 1

        data = contract.encodeABI(fn_name='swapExactTokensForETH', args=[token_amount, amount_out_min, path, to, deadline])
        # Gas estimation for the swap transaction
        gas_estimate = contract.functions.swapExactTokensForETH(
            token_amount,
            amount_out_min,
            path,
            to,
            deadline
        ).estimate_gas({
            'from': self.wallet,
            'value': 0,
        })
        transaction = {
            'to': router_address,
            'value': 0,
            'gas': gas_estimate, # using the estimated gas
            'gasPrice': gas_price,
            'nonce': nonce,
            'data': data,
            'chainId': self.web3.eth.chain_id,
            'from': self.wallet
        }

        try:
            signed_tx = self.web3.eth.account.sign_transaction(transaction, self.private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_hash_hex = tx_hash.hex()
            # tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            # if tx_receipt['status'] == 1:
            return True, tx_hash_hex
            # else:
            #     return False, tx_hash_hex
        except Exception as e:
            print(f"Error during the swap: {e}")
            return False, None

    def get_v2_pair_address(self, token_a: str, token_b: str):
        token_a = self.web3.to_checksum_address(token_a)
        token_b = self.web3.to_checksum_address(token_b)
        uniswap_v2_factory_abi = self.uniswapv2_factory_abi
        contract = self.web3.eth.contract(address=self.factory_address, abi=uniswap_v2_factory_abi)
        pair_address = contract.functions.getPair(token_a, token_b).call()
        return pair_address

    def get_v2_reserves(self, pair_address: str):
        try:
            pair_address = self.web3.to_checksum_address(pair_address)
            uniswap_v2_pair_abi = self.uniswapv2_pair_abi
            contract = self.web3.eth.contract(address=pair_address, abi=uniswap_v2_pair_abi)
            reserves = contract.functions.getReserves().call()
            return reserves
        except:
            return []

    def get_v3_positions(self, nft_address: str, owner: str):
        nft_address = self.web3.to_checksum_address(nft_address)
        owner = self.web3.to_checksum_address(owner)
        uniswap_v3_nft_abi = self.uniswapv3_nft_abi
        contract = self.web3.eth.contract(address=nft_address, abi=uniswap_v3_nft_abi)
        positions = contract.functions.positions(owner).call()
        return positions

    def get_v2_pair_tokens(self, pair_address: str):
        pair_address = self.web3.to_checksum_address(pair_address)
        uniswap_v2_pair_abi = self.uniswapv2_pair_abi
        contract = self.web3.eth.contract(address=pair_address, abi=uniswap_v2_pair_abi)
        token0 = contract.functions.token0().call()
        token1 = contract.functions.token1().call()
        return token0, token1

    def calculate_v2_price(self, token_a: str, token_b: str):
        token_a = self.web3.to_checksum_address(token_a)
        token_b = self.web3.to_checksum_address(token_b)
        pair_address = self.get_v2_pair_address(token_a, token_b)
        token0, token1 = self.get_v2_pair_tokens(pair_address)
        reserves = self.get_v2_reserves(pair_address)

        token_a_decimals = self.get_token_decimals(token_a)
        token_b_decimals = self.get_token_decimals(token_b)

        if token_a == token0:
            reserve_a = reserves[0] / (10 ** token_a_decimals)
            reserve_b = reserves[1] / (10 ** token_b_decimals)
        else:
            reserve_a = reserves[1] / (10 ** token_a_decimals)
            reserve_b = reserves[0] / (10 ** token_b_decimals)

        price = reserve_b / reserve_a
        return price
    

    def calculate_v2_price_pool(self, token_a: str, token_b: str, pair_address: str):
        token_a = self.web3.to_checksum_address(token_a)
        token_b = self.web3.to_checksum_address(token_b)
        # pair_address = self.get_v2_pair_address(token_a, token_b)
        token0, token1 = self.get_v2_pair_tokens(pair_address)
        reserves = self.get_v2_reserves(pair_address)

        token_a_decimals = self.get_token_decimals(token_a)
        token_b_decimals = self.get_token_decimals(token_b)

        if token_a == token0:
            reserve_a = reserves[0] / (10 ** token_a_decimals)
            reserve_b = reserves[1] / (10 ** token_b_decimals)
        else:
            reserve_a = reserves[1] / (10 ** token_a_decimals)
            reserve_b = reserves[0] / (10 ** token_b_decimals)

        price = reserve_b / reserve_a
        return price


    def get_token_decimals(self, token_address: str):
        token_address = self.web3.to_checksum_address(token_address)
        erc20_abi = self.erc20_abi
        contract = self.web3.eth.contract(address=token_address, abi=erc20_abi)
        decimals = contract.functions.decimals().call()
        return decimals


    def get_token_symbol(self, token_address: str):
        token_address = self.web3.to_checksum_address(token_address)
        erc20_abi = self.erc20_abi
        contract = self.web3.eth.contract(address=token_address, abi=erc20_abi)
        name = contract.functions.symbol().call()
        return name
    

    def get_token_balance(self, token_address: str):
        token_address = self.web3.to_checksum_address(token_address)
        erc20_abi = self.erc20_abi
        contract = self.web3.eth.contract(address=token_address, abi=erc20_abi)
        name = contract.functions.balanceOf(self.wallet).call()
        return name


    def swap_eth_for_usdt(self,usdt_address, usdt_amount):
        try:
        # Contract addresses
            uniswap_router_address = self.router_address
            weth_address = WETH_ADDRESS
            usdt_address = '0xdAC17F958D2ee523a2206206994597C13D831ec7'

            # Contract ABIs
            uniswap_router_abi = self.uniswapv2_router_abi
            erc20_abi = self.erc20_abi

            

            # Get the Uniswap contract
            uniswap_router = self.web3.eth.contract(address=uniswap_router_address, abi=uniswap_router_abi)

            # Estimate the amount of ETH needed
            eth_amounts = uniswap_router.functions.getAmountsIn(usdt_amount, [weth_address, usdt_address]).call()
            eth_amount = int(eth_amounts[0])
            
            # Approve the Uniswap router to spend WETH
            weth_contract = self.web3.eth.contract(address=weth_address, abi=erc20_abi)
            nonce = self.web3.eth.get_transaction_count(self.wallet)
            txn = weth_contract.functions.approve(uniswap_router_address, eth_amount).build_transaction({
                'chainId': self.web3.eth.chain_id,
                'gas': 350000,
                'gasPrice': self.web3.eth.gas_price,
                'nonce': nonce,
            })
            signed_txn = self.web3.eth.account.sign_transaction(txn, private_key=self.private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            x = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            

            nonce += 1  # Increment nonce

            # Perform the swap
            deadline = int(time.time()) + 10*60  # 10 Minutes from now
            gas = uniswap_router.functions.swapExactETHForTokens(
                    usdt_amount,
                    [weth_address, usdt_address],
                    self.wallet,
                    deadline
                ).estimate_gas({"from": self.wallet, "value": eth_amount})
            
            gas_price = self.web3.eth.gas_price
            data = uniswap_router.functions.swapExactETHForTokens(
                    usdt_amount,
                    [weth_address, usdt_address],
                    self.wallet,
                    deadline
                ).build_transaction({
                                    'from': self.wallet,
                                    'gas': gas,
                                    'gasPrice': gas_price,
                                    'nonce': nonce,
                                })['data']

            transaction = {
                'to': uniswap_router_address,
                'value': eth_amount,
                'gas': gas,
                'gasPrice': gas_price,
                'nonce': nonce,
                'data': data,
            }

            signed_tx = self.web3.eth.account.sign_transaction(transaction, self.private_key)

            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            x = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            self.get_token_balance(usdt_address)

            return True, tx_hash.hex()  # Return status and transaction hash

        except Exception as e:
            return False, str(e)  # Return status and error message

    def wrap_ether(self, amount):
        nonce = self.web3.eth.get_transaction_count(self.wallet)
        txn_dict = {
            'nonce': nonce,
            'gas': 2000000,
            'gasPrice': self.web3.eth.gas_price
        }

        weth_txn = self.weth.functions.deposit().build_transaction(txn_dict)
        weth_txn['value'] = amount  # Amount of Ether to wrap

        signed_txn = self.web3.eth.account.sign_transaction(weth_txn, private_key=self.private_key)
        result = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        return result.hex()

uniswap_base = UniswapUtils(provider_url=ETH_INFURA_URL, address=HOLDING_TOKEN_ADDRESS)
sushiswap_base = UniswapUtils(provider_url=ARB_INFURA_URL, address=HOLDING_TOKEN_ADDRESS,exchange='sushiswap')
pancakeswap_base = UniswapUtils(provider_url=ARB_INFURA_URL, address=HOLDING_TOKEN_ADDRESS,exchange='pancakeswap_v2')


def get_dex_base(network):
    if network=="ethereum":
        return uniswap_base, ETH_FEE_WALLET, 0.01
    elif network=="bsc":
        return pancakeswap_base, BSC_FEE_WALLET, 0.035
    else:
        return sushiswap_base, ARB_FEE_WALLET, 0.01