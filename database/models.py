from sqlalchemy import Column, BigInteger, String, Float, DateTime, ForeignKey, Boolean, Integer, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime


Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    username = Column((String(100)), nullable=True)
    chat_id = Column(BigInteger, nullable=False, unique=True)
    is_active = Column(Boolean, nullable=False, default=True)
    paid = Column(Boolean, nullable=False, default=False)
    joined_channel = Column(Boolean, nullable=False, default=False)
    holds_token = Column(Boolean, nullable=False, default=False)
    premium = Column(Boolean, nullable=False, default=False)
    cumulative_fee = Column(Float, nullable=False, default=0.0)
    wallets = relationship("Wallet", back_populates="user")
    copy_addresses = relationship('CopyAddress', back_populates='user')
    settings = relationship("UserSetting", uselist=False)
    active_trades = relationship("ActiveTrades", uselist=True)
    track_coins = relationship("TrackCoin", uselist=True)

    @classmethod
    def get_user(cls, user_id, session):
        return session.query(cls).filter(cls.chat_id == user_id).one_or_none()
    
    @classmethod
    def has_wallet(cls, user_id: int, session, network=None) -> bool:
        user = cls.get_user(user_id, session)
        
        if user and user.wallets:
            for wallet in user.wallets:
                if network:
                    if wallet.network.lower() == network.lower():
                        return True
                else:
                    return True
        return False
    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
    def update_from_dict(self, data: dict):
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)


class Payment(Base):
    __tablename__ = 'payments'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id'))
    deposit_address = Column(String(130), nullable=False)
    amount = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    tx_hash = Column(String(130), nullable=False)

    user = relationship("User")


class FeeTransfer(Base):
    __tablename__ = 'fee_transfer'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id'))
    wallet_address = Column(String(130), nullable=False)
    network = Column(String(50),nullable=False)
    amount = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    tx_hash = Column(String(130), nullable=False)

    user = relationship("User")



class TokenHolding(Base):
    __tablename__ = 'token_holdings'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id'))
    token_address = Column(String(130), nullable=False)
    amount = Column(Float, nullable=False)
    holding_wallet = Column(String(130), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    tx_hash = Column(String(130), nullable=False)
    user = relationship("User")


class TrackedContract(Base):
    __tablename__ = 'tracked_contracts'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id'))
    contract_address = Column(String(64), nullable=False)
    network = Column(String(50), nullable=False)
    last_checked = Column(DateTime, nullable=True)

    user = relationship("User")


class HPScan(Base):
    __tablename__ = 'hp_scan'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    ca = Column(String(64), nullable=False)
    hp = Column(Boolean, default=False)
    high_tax = Column(Boolean, default=False)


class UserSetting(Base):
    __tablename__ = 'user_settings'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id'))
    network = Column(String(20),nullable=False)
    auto_buy = Column(Boolean, nullable=False, default=True)
    auto_sell = Column(Boolean, nullable=False, default=True)
    amount_per_snipe = Column(Float, nullable=False)
    max_gas_price = Column(BigInteger, nullable=False)
    duplicate_buy = Column(Boolean, nullable=False, default=False)
    min_liquidity = Column(Float, nullable=False)
    auto_sell_tp = Column(Float, nullable=False)
    auto_sell_sl = Column(Float, nullable=False)
    slippage = Column(Float, nullable=False)
    sell_slippage = Column(Float, default=10)
    hp_toggle = Column(Boolean, nullable=False, default=True)
    copy_trade_percentage = Column(Float, nullable=False)
    # auto_slippage_settings = Column(Boolean, nullable=False, default=True)
    blocks_to_wait = Column(BigInteger, default=4)

    user = relationship("User", back_populates="settings")

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
    def update_from_dict(self, data: dict):
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)


class ActiveTrades(Base):
    __tablename__ = 'active_trades'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id'))
    network = Column(String(66), nullable=False)
    coin_name = Column(String(500), nullable=False)
    coin_symbol = Column(String(100), nullable=False)
    coin_dex = Column(String(100), nullable=False)
    price_in = Column(Float, default=0.0)
    token_address = Column(String(64), nullable=False)
    token_in_address = Column(String(64), nullable=False)
    tx_hash = Column(String(66), nullable=False)
    trade_type = Column(String(10), nullable=False)  # 'buy' or 'sell'
    amount = Column(Float, nullable=False)
    fee = Column(Float, nullable=False, default=0.0)
    token_qty = Column(Numeric, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    status = Column(Boolean, default=True)
    user = relationship("User", back_populates="active_trades")



class SmartContractStats(Base):
    __tablename__ = 'smart_contract_stats'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    contract_address = Column(String(64), nullable=False)
    network = Column(String(50), nullable=False)
    price = Column(Float, nullable=False)
    liquidity = Column(Float, nullable=False)
    total_supply = Column(BigInteger, nullable=False)
    timestamp = Column(DateTime, nullable=False)


class TrackCoin(Base):
    __tablename__ = "track_coins"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id'))
    coin_id = Column(BigInteger, ForeignKey('coins.id'))
    user = relationship("User", back_populates="track_coins", lazy='select')
    coin = relationship("Coin", back_populates="track_coins", lazy='select')


class Coin(Base):
    __tablename__ = "coins"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    contract_address = Column(String(64), unique=True, nullable=False)
    lp_address = Column(String(64), nullable=False)
    name = Column(String(1000))
    symbol = Column(String(500))
    network = Column(String(100), nullable=False)
    quote_symbol = Column(String(500))
    quote_address = Column(String(500))
    dex = Column(String(100), nullable=False)
    market_cap_dex = Column(Float, default=0.0)
    pool = Column(String(200))
    liquidity = Column(Float, default=0.0)
    price = Column(Float, default=0.0)
    price_usd = Column(Float, default=0.0)
    burnt = Column(Float, default=0.0)
    liq_weth = Column(Float, default=0.0)
    max_buy_amount = Column(Float, default=0.0)
    max_sell_amount = Column(Float, default=0.0)
    max_wallet_amount = Column(Float, default=0.0)
    market_cap = Column(Float, default=0.0)
    is_honeypot = Column(Boolean, default=False)
    is_blacklisted = Column(Boolean, default=False)
    is_anti_whale = Column(Boolean, default=False)
    cant_sell_all = Column(Boolean, default=False)
    decimals = Column(Integer, default=18)
    totalSupply = Column(BigInteger, default=18)
    buy_tax = Column(Float, default=0.0)
    sell_tax = Column(Float, default=0.0)
    is_dexscreener = Column(Boolean, default=False)
    pair_created_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    track_coins = relationship("TrackCoin", uselist=True)
    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
    def update_from_dict(self, data: dict):
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)

class Wallet(Base):
    __tablename__ = 'wallets'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id'))
    name = Column(String(100),nullable=False)
    wallet_address = Column(String(64), nullable=False)
    wallet_encrypted_seed = Column(String(500), nullable=False)
    active = Column(Boolean, default=False)
    network = Column(String(20), nullable=False)
    user = relationship("User", back_populates="wallets")


# new table for copy trading 
class CopyAddress(Base):

    __tablename__ = 'copy_addresses'

    id = Column(Integer, primary_key=True, autoincrement=True)
    address = Column(String(255), nullable=False)  # Adjust the length as needed
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    
    user = relationship("User", back_populates="copy_addresses")
    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}