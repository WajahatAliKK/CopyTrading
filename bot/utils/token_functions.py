import re

def is_token_address(text: str) -> bool:
    pattern = "^0x[a-fA-F0-9]{40}$"
    return bool(re.match(pattern, text))

def get_token_info(token_address: str):
    # Placeholder implementation, replace with actual logic
    return {
        "name": "Example Token",
        "symbol": "EXT",
        "decimals": 18,
    }
