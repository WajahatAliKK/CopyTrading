from sqlalchemy.orm import Session
from database.models import User
from typing import Optional
from aiogram import types
from bot.db_client import db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete
from database.client import Client

from sqlalchemy.orm import selectinload 

async def get_user_by_chat_id(chat_id, session):
    # return session.query(User).options(joinedload(User.wallets)).filter(User.chat_id == chat_id).one_or_none()
    async with db.AsyncSession() as session:
        result = await session.execute(
            select(User).options(selectinload(User.wallets)).where(User.chat_id == chat_id)
        )
        user = result.scalar_one_or_none()
        return user

async def get_user_by_id(id):
    # return session.query(User).options(joinedload(User.wallets)).filter(User.chat_id == chat_id).one_or_none()
    async with db.AsyncSession() as session:
        result = await session.execute(
            select(User).options(selectinload(User.wallets)).where(User.id == id)
        )
        user = result.scalar_one_or_none()
        return user

async def add_user(user_data: types.User, db: Client) -> User:
    user = User(
        username=user_data.username,
        chat_id=user_data.id,
        is_active=True,
        paid=False,
        joined_channel=False,
        holds_token=False,
        premium = False
    )
    async with db.AsyncSession() as session:
        session.add(user)
        await session.commit()
    return user

async def update_user_status(user_data: types.User, db: Client) -> Optional[User]:
    username = user_data.username
    premium = user_data.premium
    holds_token = user_data.holds_token
    async with db.AsyncSession() as session:
        result = await session.execute(
            select(User).where(User.chat_id == user_data.id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.username = username
            user.premium = premium
            user.holds_token = holds_token
            await session.commit()
            return user
    return None


async def update_user(user_data: types.User, db: Client) -> Optional[User]:
    username = user_data.username
    async with db.AsyncSession() as session:
        result = await session.execute(
            select(User).where(User.chat_id == user_data.id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.username = username
            await session.commit()
            return user
    return None


async def update_user_with_user(user: User, db):
    async with db.AsyncSession() as session:
        result = await session.execute(
            select(User).where(User.id == user.id)
        )
        old_user = result.scalar_one_or_none()
        old_user.update_from_dict(user.to_dict())
        await session.commit()

    return old_user

async def update_user_group_status(user_id, status: bool, db: Client) -> Optional[User]:
    
    async with db.AsyncSession() as session:
        result = await session.execute(
            select(User).where(User.chat_id == user_id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.joined_channel = status
            await session.commit()
            return user
    return None


async def update_user_paid_status(user_id, status: bool, db: Client) -> Optional[User]:
    
    async with db.AsyncSession() as session:
        result = await session.execute(
            select(User).where(User.chat_id == user_id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.paid = status
            await session.commit()
            return user
    return None

async def update_user_holdT_status(user_id, status: bool, db: Client) -> Optional[User]:
    
    async with db.AsyncSession() as session:
        result = await session.execute(
            select(User).where(User.chat_id == user_id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.holds_token = status
            await session.commit()
            return user
    return None


async def update_user_premium_status(user_id, status: bool, db: Client) -> Optional[User]:
    
    async with db.AsyncSession() as session:
        result = await session.execute(
            select(User).where(User.chat_id == user_id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.premium = status
            await session.commit()
            return user
    return None


async def get_user(user_data: types.User, db) -> Optional[User]:
    async with db.AsyncSession() as session:
        result = await session.execute(
            select(User).where(User.chat_id == user_data.id)
        )
        user = result.scalar_one_or_none()
        return user
    

async def toggle_user_active(user_id, db):
    async with db.AsyncSession() as session:
        result = await session.execute(
            select(User).where(User.id == user_id)
            )
        user = result.scalars().first()
        if user:
            user.is_active = not user.is_active
            await session.commit()
            return user
    return None
