from database.models import User, TokenHolding
from typing import Optional
from aiogram import types
from sqlalchemy import select, insert, update, delete




async def add_holding_buy(user_data: types.User, holdingT_data, db) -> Optional[User]:
    async with db.AsyncSession() as session:
        result = await session.execute(
            select(User).where(User.chat_id == user_data)
        )
        user = result.scalar_one_or_none()
        
        token_hold = TokenHolding(
            user_id = user.id,
            holding_wallet = holdingT_data['wallet_address'],
            amount=holdingT_data['amount'],
            timestamp=holdingT_data['timestamp'],
            token_address= holdingT_data['token_address'],
            tx_hash = holdingT_data['tx_hash']
        )
        
        
        session.add(token_hold)
        await session.commit()

        return user
    
