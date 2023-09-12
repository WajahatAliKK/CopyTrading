from typing import Optional
from aiogram import types
from sqlalchemy import select
from database.models import User, Coin, TrackCoin
from typing import List
from sqlalchemy.orm import selectinload
from sqlalchemy import select, and_
from datetime import datetime



async def add_tracking(coin, user, db) -> Optional[TrackCoin]:
    async with db.AsyncSession() as session:
        
        tracking = await session.execute(
            select(TrackCoin).where(
                (TrackCoin.user_id == user.id) &
                (TrackCoin.coin_id == coin.id)
            )
        )
        tracking = tracking.scalar_one_or_none()

        if not tracking:
        

            tracking = TrackCoin(
                coin_id = coin.id,
                user_id = user.id
                
            )
        
            session.add(coin)
        
            await session.commit()

        return tracking

async def get_tracking_by_user(user, db) -> Optional[TrackCoin]:
    async with db.AsyncSession() as session:
        
        tracking = await session.execute(
            select(TrackCoin).where(
                (TrackCoin.user_id == user.id) 
                
            )
        )
        tracking = tracking.scalars().all()
        return tracking


async def get_tracking_by_coin(coin, db) -> Optional[TrackCoin]:
    async with db.AsyncSession() as session:
        
        tracking = await session.execute(
            select(TrackCoin).where(
                (TrackCoin.coin_id == coin.id) 
                
            )
        )
        tracking = tracking.scalars().all()
        return tracking


async def get_single_tracking(coin, user, db) -> Optional[TrackCoin]:
    async with db.AsyncSession() as session:
        
        tracking = await session.execute(
            select(TrackCoin).where(
                (TrackCoin.user_id == user.id) &
                (TrackCoin.coin_id == coin.id)
            )
        )
        tracking = tracking.scalar_one_or_none()
        return tracking


async def add_coin_data(coin_data: dict, db) -> Optional[Coin]:
    async with db.AsyncSession() as session:
        # Check if a coin already exists with this contract address
        existing_coin = await session.execute(
            select(Coin).where(
                Coin.contract_address == coin_data['contract_address'],
            )
        )
        existing_coin = existing_coin.scalar_one_or_none()

        

        coin = Coin(
            contract_address=coin_data['contract_address'].lower(),
            lp_address=coin_data['pair_address'],
            name=coin_data['name'],
            symbol=coin_data['symbol'],
            network=coin_data['network'],
            quote_symbol=coin_data['quote_symbol'],
            quote_address=coin_data['quote_address'],
            dex=coin_data['dex'],
            market_cap_dex=coin_data.get('market_cap', 0.0),
            price = coin_data.get('price', 0.0),
            price_usd = coin_data.get('price_usd', 0.0),
            pool="V2",
            liquidity=coin_data.get('liquidity', 0.0),
            # burnt=coin_data.get('burnt', 0.0),
            is_dexscreener=coin_data['dexscreener'],
            # liq_weth=coin_data.get('liq_weth', 0.0),
            max_buy_amount=coin_data.get('maxWallet_perc', 0.0),
            max_sell_amount=coin_data.get('maxWallet_perc', 0.0),
            max_wallet_amount=coin_data.get('maxWallet_perc', 0.0),
            market_cap=coin_data.get('market_cap', 0.0),
            is_honeypot=coin_data.get('is_honeypot', False),
            is_blacklisted=coin_data.get('is_blacklisted', False),
            is_anti_whale=coin_data.get('anti_whale', False),
            cant_sell_all=coin_data.get('sell_limit', False),
            decimals=coin_data.get('decimals', 18),
            totalSupply=coin_data.get('total_supply', 18),
            buy_tax=coin_data.get('buy_tax', 0.0) if coin_data.get('buy_tax')!='' else 0,
            sell_tax=coin_data.get('sell_tax', 0.0)  if coin_data.get('sell_tax')!='' else 0,
            pair_created_at=coin_data.get('created_at', datetime.utcnow()),
            # created_at=coin_data.get('created_at', datetime.utcnow()),
        )
        if existing_coin:
            # Update all attributes of the existing coin
            for attr, value in coin.__dict__.items():
                if attr != '_sa_instance_state':  # Ignore SQLAlchemy specific attribute
                    setattr(existing_coin, attr, value)
            await session.merge(existing_coin) 
            await session.flush()
        else:
            # Add a new coin
            session.add(coin)
        
        await session.commit()

        return coin


async def update_coin_data(setting: Coin, db):
    async with db.AsyncSession() as session:
        result = await session.execute(
            select(Coin).where(Coin.id == setting.id)
        )
        old_setting = result.scalar_one_or_none()
        old_setting.update_from_dict(setting.to_dict())
        await session.commit()

    return old_setting

async def get_coin(contract_address, db) -> Coin:
    async with db.AsyncSession() as session:
        result = await session.execute(
            select(Coin).where(Coin.contract_address == contract_address)
        )
        coin = result.scalars().first()
        return coin
    


async def get_coin_by_id(coin_id, db) -> Coin:
    async with db.AsyncSession() as session:
        result = await session.execute(
            select(Coin).where(Coin.id == coin_id)
        )
        coin = result.scalars().first()
        return coin

async def get_users_tracking_coin(contract_address, db):
    
    async with db.AsyncSession() as session:
        coin = await get_coin(contract_address, db)
        if coin:
            return [track_coin.user_id for track_coin in coin.track_coins]

    
    return []
