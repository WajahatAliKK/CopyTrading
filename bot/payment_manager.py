import time
from web3 import Web3
from sqlalchemy.orm import Session
from bot.models import User, Payment
from bot.database import Database

class PaymentManager:
    def __init__(self, db: Database, admin_wallet_address: str, network: str = "ethereum"):
        self.db = db
        self.network = network
        self.admin_wallet_address = admin_wallet_address

        # Set up the Web3 instance based on the network
        if network == "ethereum":
            self.w3 = Web3(Web3.HTTPProvider('https://mainnet.infura.io/v3/YOUR-PROJECT-ID'))
        elif network == "binance_smart_chain":
            self.w3 = Web3(Web3.HTTPProvider('https://bsc-dataseed1.binance.org'))
        # Add other networks as needed

    def check_incoming_payments(self, poll_interval: int = 60):
        while True:
            session = self.db.get_session()
            users = session.query(User).filter(User.paid == False).all()

            for user in users:
                deposit_address = user.deposit_address
                balance = self.w3.eth.getBalance(deposit_address)

                if balance > 0:
                    self.handle_payment(user, balance, session)

            session.close()
            time.sleep(poll_interval)

    def handle_payment(self, user: User, amount: int, session: Session):
        # Forward the payment to the admin wallet
        deposit_private_key = user.deposit_private_key
        deposit_address = user.deposit_address
        nonce = self.w3.eth.getTransactionCount(deposit_address)

        gas_price = self.w3.eth.gasPrice
        gas = 21000
        total_gas_fee = gas * gas_price

        transaction = {
            'to': self.admin_wallet_address,
            'value': amount - total_gas_fee,
            'gas': gas,
            'gasPrice': gas_price,
            'nonce': nonce,
        }

        signed_tx = self.w3.eth.account.signTransaction(transaction, deposit_private_key)
        self.w3.eth.sendRawTransaction(signed_tx.rawTransaction)

        # Store the payment in the database
        payment = Payment(user_id=user.id, amount=self.w3.fromWei(amount, 'ether'))
        session.add(payment)
        session.commit()

        # Update the user's paid status
        user.paid = True
        session.commit()
