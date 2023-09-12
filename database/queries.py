# from database import Session
from database.models import User, Payment, TokenHolding, Subscription, TrackedContract, UserSetting, SmartContractStats
from sqlalchemy.orm import Session



def add_user(user_data, db_session: Session):
    user = User(
        username=user_data.username,
        chat_id=user_data.id,
        is_active=True,
        paid=False,
        joined_channel=False,
        holds_token=False
    )
    db_session.add(user)
    db_session.commit()
    return user

def update_user(user_id: int, paid: bool, joined_channel: bool, holds_token: bool, db_session: Session):
    user = db_session.query(User).filter(User.chat_id == user_id).first()
    if user:
        user.paid = paid
        user.joined_channel = joined_channel
        user.holds_token = holds_token
        db_session.commit()
    return user



def create_new_wallet(chat_id, network):
    # TODO: Generate the new wallet and encrypted seed using the Wallet Manager
    wallet_address = None
    encrypted_seed = None

    db = Session()
    user = User(chat_id=chat_id, network=network, wallet_address=wallet_address, wallet_encrypted_seed=encrypted_seed)
    db.add(user)
    db.commit()

    return wallet_address, encrypted_seed

def connect_existing_wallet(chat_id, network, wallet_address):
    db = Session()
    user = User(chat_id=chat_id, network=network, wallet_address=wallet_address)
    db.add(user)
    db.commit()

# async def add_coin(contract_address: str, name: str, symbol: str) -> Coin:
#     coin = Coin(contract_address=contract_address, name=name, symbol=symbol)
#     async with session.begin():
#         session.add(coin)
#     return coin


# async def get_coin_by_address(contract_address: str) -> Optional[Coin]:
#     async with session.begin():
#         coin = await session.get(Coin, contract_address)
#     return coin

# async def get_users_with_active_subscriptions_and_auto_buy() -> List[User]:
#     async with session.begin():
#         users = (
#             await session.execute(
#                 select(User)
#                 .where(User.subscription_active == True)
#                 .where(User.auto_buy_enabled == True)
#             )
#         ).scalars().all()
#     return users
