from typing import Optional
from aiogram import types
from sqlalchemy import select
from database.models import User, UserSetting, Wallet
from typing import List
from sqlalchemy.orm import selectinload
from sqlalchemy import select, and_

async def add_user_settings(user_data: types.User, settings_data, db) -> Optional[UserSetting]:
    async with db.AsyncSession() as session:
        result = await session.execute(
            select(User).where(User.chat_id == user_data.id)
        )
        user = result.scalar_one_or_none()
        if user:
            # Check if a setting already exists for this user ID and network
            existing_setting = await session.execute(
                select(UserSetting).where(
                    UserSetting.user_id == user.id,
                    UserSetting.network == settings_data['network']
                )
            )
            existing_setting = existing_setting.scalar_one_or_none()

            if existing_setting:
                return None  # Setting already exists, do not create a new one

            user_setting = UserSetting(
                user_id=user.id,
                network=settings_data['network'],
                auto_buy=settings_data['auto_buy'],
                auto_sell=settings_data['auto_sell'],
                amount_per_snipe=settings_data['amount_per_snipe'],
                max_gas_price=settings_data['max_gas_price'],
                duplicate_buy=settings_data['duplicate_buy'],
                min_liquidity=settings_data['min_liquidity'],
                auto_sell_tp = settings_data['auto_sell_tp'],
                auto_sell_sl = settings_data['auto_sell_sl'],
                sell_slippage = settings_data['sell_slippage'],
                slippage=settings_data['slippage'],
                hp_toggle=True,
                
                blocks_to_wait=settings_data.get('blocks_to_wait', 4)
            )

            session.add(user_setting)
            await session.commit()

        return user_setting


async def get_user_settings(chat_id, network, db):
    async with db.AsyncSession() as session:
        result = await session.execute(
            select(User).where(User.chat_id == chat_id)
        )
        user = result.scalar_one_or_none()
        if user:
            result = await session.execute(
                (select(UserSetting).where(
                    (UserSetting.user_id == user.id) &
                    (UserSetting.network == network)
                ))

            )
            setting = result.scalar_one_or_none()

        return setting

async def get_user_settings_by_user(user, network, db, user_id=None) -> UserSetting: 
    async with db.AsyncSession() as session:
        if not user_id:
            user_id = user.id
        result = await session.execute(
            (select(UserSetting).where(
                (UserSetting.user_id == user_id) &
                (UserSetting.network == network)
            ))

        )
        setting = result.scalars().first()

        return setting


async def set_user_setting(setting: UserSetting, db):
    async with db.AsyncSession() as session:
        result = await session.execute(
            select(UserSetting).where(UserSetting.id == setting.id)
        )
        old_setting = result.scalar_one_or_none()
        old_setting.update_from_dict(setting.to_dict())
        await session.commit()

    return old_setting



# async def get_active_users_with_settings(network: str, db) -> List[User]:
#     async with db.AsyncSession() as session:
#         result = await session.execute(
#             select(User)
#             .distinct(User.id)
#             .options(selectinload(User.settings), selectinload(User.wallets))
#             .join(UserSetting, UserSetting.user_id == User.id)
#             .join(Wallet, Wallet.user_id == User.id)
#             .where(
#                 (User.is_active == True)
#                 & (UserSetting.network == network)
#                 & (UserSetting.auto_buy == True)
#                 & ((User.paid == True) | (User.joined_channel == True))
#                 & (Wallet.active == True)
#                 & (Wallet.network == network)
#             )
#         )
#         users = result.scalars().all()
#         return users



async def get_active_users_with_settings(network: str, db) -> List[User]:
    async with db.AsyncSession() as session:
        result = await session.execute(
            select(User)
            .options(selectinload(User.settings), selectinload(User.wallets))
            .join(UserSetting, UserSetting.user_id == User.id)
            .join(Wallet, Wallet.user_id == User.id)
            .where(
                (User.is_active == True)
                & (UserSetting.network == network & UserSetting.auto_buy == True)
                & ((User.joined_channel == True))
                & (Wallet.active == True)
                & (Wallet.network == network)
            ).distinct()
        )
        users = result.scalars().all()
        return users


async def get_active_paid_users(db) -> Optional[Wallet]:
    async with db.AsyncSession() as session:
        result = await session.execute(
            select(User).where(
            # ((User.paid == True) | (User.holds_token == True) | (User.premium == True)) & 
            (User.is_active == True)
        )
        
        )
        users = result.scalars().all()
        
        return users
    
