# from database.models import User
from typing import Optional
from aiogram import types
from bot.db_client import db
from sqlalchemy.orm import selectinload 
from database.models import CopyAddress , User, UserSetting
from sqlalchemy import select, insert, update, delete

async def addcopytradingaddress(userchat_id : str , user_address:str):
    async with db.AsyncSession() as session:
        result = await session.execute(select(User).where(User.chat_id == userchat_id))
        user = result.scalar_one_or_none()
        if user:
          cp = CopyAddress(
                address = user_address,
                user_id = user.id
                )
          session.add(cp)
          await session.commit()
          return True
        return False

async def deletecopyaddress(userchat_id: str , user_address:str):
   async with db.AsyncSession() as session:
        result = await session.execute(select(User).where(User.chat_id == userchat_id))
        user = result.scalar_one_or_none()
        if user:
            target_row = await session.execute(select(CopyAddress).filter(
                (CopyAddress.user_id == user.id) & (CopyAddress.address == user_address)))
            copy_address = target_row.scalar()
           
            if copy_address :
                await session.delete(copy_address)
                await session.commit()
                return True       
            
        return False
   
async def updateCopyTradePercentage(user_id: str, percentage: str):
    async with db.AsyncSession() as session:
      
        print(percentage)
        userid_fromuser = await session.execute(select(User.id).where(User.chat_id == user_id))
        userid_fromuser = userid_fromuser.scalar_one_or_none()

    

        stmt = select(UserSetting).filter(UserSetting.user_id == userid_fromuser)
        user_settings = await session.execute(stmt)
        user_setting = user_settings.scalar_one_or_none()

        if user_setting:

            user_setting.copy_trade_percentage = percentage

        await session.commit()
            
                

async def get_no_of_addresses(userchat_id:str):
    async with db.AsyncSession() as session:
        result = await session.execute(select(User).where(User.chat_id == userchat_id))
        user = result.scalar_one_or_none()
        result = await session.execute(select(CopyAddress.address).where(CopyAddress.user_id == user.id))
        addresses = result.scalars().all()
        if addresses:
            total_len = len(addresses)

            return addresses, total_len
        else:
            return 0 , 0 


async def getAddresses():
    async with db.AsyncSession() as session:
        result = await session.execute(select(CopyAddress))
        addresses = result.scalars().all()
        if addresses:
            return addresses
        else:
            return False


async def get_percentgae_of_copy_trade(users_IID):
    async with db.AsyncSession() as session:

    
        userid_fromuser = await session.execute(select(User.id).where(User.chat_id == users_IID))
        userid_fromuser = userid_fromuser.scalar_one_or_none()

        
        user_percentage  = await session.execute(select(UserSetting.copy_trade_percentage).where(UserSetting.user_id == userid_fromuser))
        user_percentage = user_percentage.scalar_one_or_none()
        
        return user_percentage