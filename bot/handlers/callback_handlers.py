from telegram import Update
from telegram.ext import CallbackContext

from database.queries import create_new_wallet, connect_existing_wallet

def generate_new_wallet_callback(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    network = context.user_data.get("network")

    if not network:
        # TODO: Ask for the network before generating the new wallet
        return

    wallet_address, encrypted_seed = create_new_wallet(chat_id, network)
    
    # TODO: Send the wallet address and encrypted seed to the user

def connect_existing_wallet_callback(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    network = context.user_data.get("network")

    if not network:
        # TODO: Ask for the network before connecting an existing wallet
        return

    # TODO: Ask the user for their wallet address
    wallet_address = None

    # TODO: Check if the wallet address is valid before connecting
    if wallet_address:
        connect_existing_wallet(chat_id, network, wallet_address)
        # TODO: Send a success message to the user
    else:
        # TODO: Send an error message to the user
