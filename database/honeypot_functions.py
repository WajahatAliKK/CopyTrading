from database.models import HPScan
from typing import Optional
from aiogram import types
from sqlalchemy import select, insert, update, delete



async def update_hp_contract(data: types.User, db) -> HPScan:
    
    async with db.AsyncSession() as session:
        result = await session.execute(
            select(HPScan).where(HPScan.ca == data['ca'].lower())
        )
        cat = result.scalars()
        if cat:
            cat = cat.first()
        
        if not cat:
            cat = HPScan(
                ca= data['ca'].lower(),
                hp= data['hp'],
                high_tax = data['high_tax']
            )
        
            session.add(cat)
            
        else:
            cat.hp = data['hp']
            cat.high_tax = data['high_tax']
        await session.commit()

        
    return cat


async def get_hp_contract(contract_address, db) -> HPScan:
    
    async with db.AsyncSession() as session:
        result = await session.execute(
            select(HPScan).where(HPScan.ca == contract_address.lower())
        )
        cat = result.scalars()
        if cat:
            cat = cat.first()
        
        return cat