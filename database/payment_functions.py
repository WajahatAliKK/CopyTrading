from database.models import User, Payment, FeeTransfer
from typing import Optional
from aiogram import types
from sqlalchemy import select, insert, update, delete




async def add_payment(user_data: types.User, payment_data, db) -> Optional[User]:
    async with db.AsyncSession() as session:
        result = await session.execute(
            select(User).where(User.chat_id == user_data)
        )
        user = result.scalar_one_or_none()
        
        payment = Payment(
            user_id = user.id,
            deposit_address = payment_data['wallet_address'],
            amount=payment_data['amount'],
            timestamp=payment_data['timestamp'],
            tx_hash = payment_data['tx_hash']
        )
        
        
        session.add(payment)
        await session.commit()

        return user
    
async def add_fee_payment(chat_id: int, payment_data, db) -> Optional[FeeTransfer]:
    async with db.AsyncSession() as session:
        result = await session.execute(
            select(User).where(User.chat_id == chat_id)
        )
        user = result.scalar_one_or_none()
        
        payment = FeeTransfer(
            user_id = user.id,
            wallet_address = payment_data['wallet_address'],
            network=payment_data['network'],
            amount=payment_data['amount'],
            timestamp=payment_data['timestamp'],
            tx_hash = payment_data['tx_hash']
        )
        
        
        session.add(payment)
        await session.commit()

        return payment