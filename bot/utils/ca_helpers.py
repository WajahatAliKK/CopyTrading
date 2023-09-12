
import requests, json
from bot.utils.config import ETHERSCAN_API, BSCSCAN_API, ARBISCAN_API, WETH_ADDRESS, WBNB_ADDRESS, WETH_ADDRESS_ARB
from bot.uniswap_utils import uniswap_base, pancakeswap_base, sushiswap_base
from datetime import datetime
from database.models import Coin
import concurrent.futures

NETWORK_TOKEN_MAPPING = {
    "ethereum": "WETH",
    "bsc": "WBNB",
    "arbitrum": "WETH",
}

import requests

NETWORK_TOKEN_MAPPING = {
    "ethereum": "WETH",
    "bsc": "WBNB",
    "arbitrum": "WETH",
}

def fetch_token_info(contract_address):
    try:
        response = requests.get(f'https://api.dexscreener.com/latest/dex/tokens/{contract_address}')
        response.raise_for_status()
        data = response.json()
        pair = None
        # Filter pairs by network and matching quoteToken symbol
        
        for pair1 in data.get('pairs', []):
            
            if pair1.get('quoteToken', {}).get('symbol') in ["WETH","WBNB"]:
                pair = pair1
                break
            elif pair1.get('baseToken', {}).get('symbol') in ["WETH","WBNB"] and pair1.get('quoteToken', {}).get('address').lower() == contract_address.lower() :
                pair = pair1
                pair['baseToken'],pair['quoteToken'] = pair['quoteToken'], pair['baseToken']
                pair['priceNative'] = 1/float(pair['priceNative'])
                pair['priceUsd'] = 1/float(pair['priceUsd'])
                break
                # Extract necessary details
        if not pair:
            for pair1 in data.get('pairs', []):
                if pair1.get('baseToken', {}).get('address').lower() == contract_address.lower():
                    pair = pair1
                    break
        if pair:
            token_info = {
                        "contract_address": contract_address,
                        "name": pair.get('baseToken', {}).get('name'),
                        "symbol": pair.get('baseToken', {}).get('symbol'),
                        "quote_symbol": pair.get('quoteToken', {}).get('symbol'),
                        "quote_address": pair.get('quoteToken', {}).get('address'),
                        "liquidity": pair.get('liquidity', {}).get('quote'),  # liquidity in quote currency
                        "market_cap": pair.get('liquidity', {}).get('usd'),
                        "pair_address": pair.get('pairAddress'),  # pair address
                        "created_at": pair.get('pairCreatedAt'),
                        "chart_url" : pair.get('url'),
                        'price':  pair.get('priceNative'),
                        'price_usd': pair.get('priceUsd'),
                        'network': pair.get('chainId'),
                        'dex': pair.get('dexId'),
                        'dexscreener': True
                    }
            if token_info['created_at']:
                timestamp_s = int(token_info['created_at'])/1000
                token_info['created_at'] = datetime.utcfromtimestamp(timestamp_s)
            
                return token_info
        return None
    except Exception as e:
        print(f"Error while fetching token info: {e}")
        return None


def to_check_sum(contract_address):
    return uniswap_base.web3.to_checksum_address(contract_address)


def generate_message(coin: Coin, tracking, balance):
    unit_map = {
        "ethereum": "ETH",
        "bsc": "BNB",
        "arbitrum": "ETH",
    }

    unit = unit_map.get(coin.network, "ETH")
    address = "etherscan.io" if coin.network=="ethereum" else ("bscscan.com" if coin.network=="bsc" else "arbiscan.io")
    
    message = (
        f"🔍 Tracking | {'✅' if tracking else '❌'}\n"
        f"🪙 {coin.name.strip()} (#{coin.symbol}) 🔗 {unit} Token\n"
        f"[CA](https://{address}/token/{coin.contract_address}): `{coin.contract_address}`\n"
        f"[LP](https://{address}/token/{coin.lp_address}): `{coin.lp_address}`\n"
        f"💰 Balance | {balance} {coin.symbol}\n"
        f"💧 Liquidity | {coin.liquidity} W{unit}\n"
        f"🧢 Market Cap | ${coin.market_cap}\n"
        f"-MC/Liq: {round(coin.market_cap/coin.liquidity,2) if coin.liquidity>0 else 0}\n"
        f"-Max Wallet: {coin.max_wallet_amount if coin.max_wallet_amount >0 else 100}% Ξ {0.01*coin.max_wallet_amount*coin.totalSupply if coin.max_wallet_amount>0 else ''} {coin.symbol if coin.max_wallet_amount>0 else ''}\n"
        f"⚖️ Taxes | 🅑 {round(float(coin.buy_tax)*100,1)}% 🅢 {round(float(coin.sell_tax)*100,1)}%\n"
        f"⚠️ Honeypot | {'Yes' if coin.is_honeypot else 'No'}\n"
    )
    return message




def get_token_abi(contract_address, network):
    if network=="ethereum":
        url = f"https://api.etherscan.io/api?module=contract&action=getabi&address={contract_address}&apikey={ETHERSCAN_API}"
    elif network=="bsc":
        url = f"https://api.bscscan.com/api?module=contract&action=getabi&address={contract_address}&apikey={BSCSCAN_API}"
    else:
        url = f"https://api.arbiscan.io/api?module=contract&action=getabi&address={contract_address}&apikey={ARBISCAN_API}"
    try:
        abi = requests.get(url).content
        abi = json.loads(abi).get('result',{})
        if abi:
            abi = json.loads(abi)
            return abi
        
    except:
        return {}

def find_relevant_function_names_from_abi(abi):
    function_names = []
    for item in abi:
        if item['type'] == 'function' and item['stateMutability'] in ['view', 'pure'] and not item['inputs']:
            function_name = item['name'].lower()  # convert to lowercase for comparison
            if any(substring in function_name for substring in ["buy", "sell", "buyer", "seller", "fee", "maxwallet"]):
                function_names.append(item['name'])
    return function_names 

def call_contract_function(contract, function_name):
    function_to_call = getattr(contract.functions, function_name)
    result = function_to_call().call()
    return result



def get_security_info(contract_address, network, d):
    if network=="ethereum":
        nid = 1
    elif network=="bsc":
        nid = 56
    else:
        nid = 42161
    url = f"https://api.gopluslabs.io/api/v1/token_security/{str(nid)}?contract_addresses={contract_address}"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    
    data  = data.get('result').get(contract_address.lower())
    
    if data:
        d['buy_tax'] = data.get("buy_tax",0)
        d['sell_tax'] = data.get("sell_tax",0)
        d['sell_limit'] = True if data.get("cannot_sell_all",0) == "1" else False
        d['anti_whale'] = True if data.get("is_anti_whale",0) == "1" else False
        d['is_honeypot'] = True if data.get("is_honeypot",0) == "1" else False
        d['is_blacklisted'] = True if data.get("is_blacklisted",0) == "1" else False
    return d



def fetch_data(contract_address, quote_symbol, quote, network, dex, base):
    try:
        data = {
            'pair_address': base.get_v2_pair_address(contract_address, quote),
            'contract_address': contract_address,
            'name': base.web3.eth.contract(contract_address, abi=base.erc20_abi).functions.name().call(),
            'symbol': base.web3.eth.contract(contract_address, abi=base.erc20_abi).functions.symbol().call(),
            'network': network,
            'dex': dex,
            'quote_symbol': quote_symbol,
            'quote_address': quote
        }
    except:
        return None
    return data

def find_max_wallet(fn, token_contract):
    try:
        if 'max' in fn.lower() and 'wallet' in fn.lower():
            return call_contract_function(token_contract, fn)
    except:
        pass
    return None

# def process_erc20_token(contract_address, network):
#     base_list = [('WETH', WETH_ADDRESS, 'ethereum', 'uniswap', uniswap_base),
#                  ('WBNB', WBNB_ADDRESS, 'bsc', 'pancakeswap', pancakeswap_base),
#                  ('WETH', WETH_ADDRESS_ARB, 'arbitrum', 'sushiswap', sushiswap_base)]

#     data = fetch_token_info(contract_address)
#     if not data:
#         with concurrent.futures.ThreadPoolExecutor() as executor:
#             futures = [executor.submit(fetch_data, contract_address, *base) for base in base_list]
#             for future in concurrent.futures.as_completed(futures):
#                 data = future.result()
#                 if data:
#                     break

#     network = data.get('network')
#     abi = get_token_abi(contract_address, network)

#     if not abi or "decimal" not in str(abi):
#         abi = base_list[0][4].erc20_abi  # Using Uniswap's abi as default.

#     web3_map = {base_list[i][2]: base_list[i][4].web3 for i in range(3)}
#     token_contract = web3_map.get(network, base_list[2][4].web3).eth.contract(contract_address, abi=abi)

#     decimals = token_contract.functions.decimals().call()
#     total_supply = token_contract.functions.totalSupply().call()

#     list_of_funcs = find_relevant_function_names_from_abi(abi)

#     max_wallet = 0
#     with concurrent.futures.ThreadPoolExecutor() as executor:
#         futures = [executor.submit(find_max_wallet, fn, token_contract) for fn in list_of_funcs]
#         for future in concurrent.futures.as_completed(futures):
#             result = future.result()
#             if result:
#                 max_wallet = result
#                 break

#     data.update({
#         'decimals': decimals,
#         'total_supply': int(total_supply/(10**decimals)),
#         'maxWallet': max_wallet,
#         'network': network,
#         'maxWallet_perc': 100*max_wallet/total_supply
#     })
#     try:
#         data = get_security_info(contract_address, network, data)
#     except Exception as e:
#         pass

#     return data

def process_erc20_token(contract_address, network):
    
    try:
        data = fetch_token_info(contract_address)
    except Exception as e:
        print(e)
        data = {}
        
    
    if data:
        
        network = data['network']
        
        try:
            abi = get_token_abi(contract_address, network)
        except Exception as e:
            print(e)
            abi = None
        if not abi:
            abi = uniswap_base.erc20_abi
        elif "decimal" not in str(abi):
            abi = uniswap_base.erc20_abi
        if network=="ethereum":
            token_contract = uniswap_base.web3.eth.contract(contract_address, abi=abi)
        elif network=="bsc":
            
            token_contract = pancakeswap_base.web3.eth.contract(contract_address, abi=abi)
        else:
            token_contract = sushiswap_base.web3.eth.contract(contract_address, abi=abi)
        decimals = token_contract.functions.decimals().call()
        total_supply = (token_contract.functions.totalSupply().call())
    else:
        
        abi = uniswap_base.erc20_abi
        
        data = {'contract_address':contract_address}
        for i,base in enumerate([uniswap_base,pancakeswap_base,sushiswap_base]):
            try:
                if i==0:
                    quote_symbol = "WETH"
                    quote = WETH_ADDRESS
                    network = "ethereum"
                    dex = "uniswap"
                elif i==1:
                    quote_symbol = "WBNB"
                    quote= WBNB_ADDRESS
                    network = "bsc"
                    dex = "pancakeswap"
                else:
                    quote_symbol = "WETH"
                    quote = WETH_ADDRESS_ARB
                    network = "arbitrum"
                    dex = "sushiswap"
                data['pair_address'] = base.get_v2_pair_address(contract_address, quote)
                token_contract = base.web3.eth.contract(contract_address, abi=abi)
                decimals = token_contract.functions.decimals().call()
                total_supply = (token_contract.functions.totalSupply().call())
                data['name']  = token_contract.functions.name().call()
                data['symbol'] = token_contract.functions.symbol().call()
                data['network'] = network
                data['dex'] = dex

                data['dexscreener'] = False
                data['quote_symbol'] = quote_symbol
                data['quote_address'] = quote
                break
            except:
                continue
        
    

    list_of_funcs = find_relevant_function_names_from_abi(abi)
    
    maxWallet = 0
    for fn in list_of_funcs:
        if 'max' in fn.lower() and 'wallet' in fn.lower():
            try:
                maxWallet = call_contract_function(token_contract, fn)
                break
            except Exception as e:
                pass
       
    

    # if data:
    data['decimals'] = decimals
    data['total_supply'] = int(total_supply/(10**decimals))
    data['maxWallet'] = maxWallet
    data['maxWallet_perc'] = 100*maxWallet/total_supply
    try:
        data = get_security_info(contract_address, network, data)
    except Exception as e:
        pass
    
    return data

