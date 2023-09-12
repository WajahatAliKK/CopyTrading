from web3 import Web3
from eth_account import Account
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import base64
from eth_account.hdaccount import mnemonic
from mnemonic import Mnemonic
import binascii
from eth_account import Account
from bip32 import BIP32

class WalletManager:

    def __init__(self, network_url: str, encryption_key: str):
        self.web3 = Web3(Web3.HTTPProvider(network_url))
        self.encryption_key = bytes.fromhex(encryption_key)

    def generate_new_address(self):
        mnemo = Mnemonic("english")
        seed_phrase  = mnemo.generate(strength=256)
        # seed_phrase = mnemo.to_mnemonic(entropy)
        # Derive seed from the seed phrase
        seed = Mnemonic.to_seed(seed_phrase)

        # Create a BIP32 master key from the seed
        bip32_master_key = BIP32.from_seed(seed)

        # Derive the first private key from the master key
        derived_path = "m/44'/60'/0'/0/0"  # Example derivation path for Ethereum
        private_key_bytes = bip32_master_key.get_privkey_from_path(derived_path)

        # Convert the private key bytes to a hexadecimal string
        private_key = binascii.hexlify(private_key_bytes).decode()

        # Create an Account object using the private key
        account = Account.from_key(private_key)

        # print("Seed phrase:", seed_phrase)
        # print("Private key:", private_key)
        # print("Encrypted:", self.encrypt_seed(private_key))
        # print("Decrypted:", self.decrypt_seed(self.encrypt_seed(private_key)))
        # print("Ethereum address:", account.address)
        return seed_phrase, private_key, account.address

    def get_eth_address(self, private_key: str):
        return Account.from_key(private_key).address
    def create_new_wallet(self):
        account = Account.create()
        address = account.address
        private_key = account.privateKey.hex()
        encrypted_seed = self.encrypt_seed(private_key)
        seed_phrase = mnemonic.to_mnemonic(private_key)
        return {
            'address': address,
            'encrypted_seed': encrypted_seed,
            'private_key': private_key,
            'seed_phrase': seed_phrase
        }

    def get_balance(self, address: str):
        balance = self.web3.eth.get_balance(address)
        return self.web3.from_wei(balance, 'ether')

    def register_existing_wallet(self, seed_phrase: str):
        account = Account.from_key(seed_phrase)
        address = account.address
        encrypted_seed = self.encrypt_seed(seed_phrase)

        return {
            'address': address,
            'encrypted_seed': encrypted_seed
        }

    def encrypt_seed(self, seed: str) -> str:
        cipher = AES.new(self.encryption_key, AES.MODE_EAX)
        ciphertext, tag = cipher.encrypt_and_digest(seed.encode())
        nonce = cipher.nonce
        return base64.b64encode(nonce + tag + ciphertext).decode()

    def decrypt_seed(self, encrypted_seed: str) -> str:
        data = base64.b64decode(encrypted_seed)
        nonce, tag, ciphertext = data[:16], data[16:32], data[32:]
        cipher = AES.new(self.encryption_key, AES.MODE_EAX, nonce)
        seed = cipher.decrypt_and_verify(ciphertext, tag)
        return seed.decode()
