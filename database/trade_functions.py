from typing import Optional
from aiogram import types
from sqlalchemy import select
from database.models import User, UserSetting, Wallet, ActiveTrades
from typing import List



async def store_active_trade(user_id: int, network: str, token_address: str, token_in_address: str, tx_hash: str, trade_type: str, amount: float, name, symbol, dex, price, balance, db):
    async with db.AsyncSession() as session:
        active_trade = ActiveTrades(
            user_id=user_id,
            network = network,
            coin_name = name,
            coin_symbol = symbol,
            coin_dex = dex,
            price_in = price,
            token_address=token_address,
            token_in_address = token_in_address,
            tx_hash=tx_hash,
            trade_type=trade_type,
            amount=amount,
            token_qty = balance,
        )
        session.add(active_trade)
        await session.commit()

async def get_trades_by_user_id(user_id: int, db):
    async with db.AsyncSession() as session:
        result = await session.execute(
            select(ActiveTrades).where(
            (ActiveTrades.user_id == user_id) &
            (ActiveTrades.status == 1)
            )
        )
        trades = result.scalars().all()
        return trades
    




async def set_trade_status_by_id(trade_id, db):
    async with db.AsyncSession() as session:
        result = await session.execute(
            select(ActiveTrades).where(ActiveTrades.id == trade_id)
        )
        trade = result.scalar_one_or_none()
        trade.status = not trade.status
        await session.commit()

        return trade

async def update_trade_balance(trade, balance, db):
    async with db.AsyncSession() as session:
        trade.token_qty = balance
        # await session.delete(trade)
        await session.commit()
        return



async def delete_trade(trade, db):
    async with db.AsyncSession() as session:
        await session.delete(trade)
        await session.commit()
        return
    

async def delete_trade_by_id(trade_id: int, db):
    async with db.AsyncSession() as session:
        result = await session.execute(
            select(ActiveTrades).where(
            (ActiveTrades.id == trade_id)
            )
        )
        trade = result.scalar_one_or_none()
        trade.status = False
        await session.commit()
        return trade
