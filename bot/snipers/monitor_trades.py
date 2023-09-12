import asyncio
from bot.db_client import db
from sqlalchemy import select
from database.models import User, UserSetting, ActiveTrades

from bot.utils.wallet_methods import eth_uni_m, eth_uni_mv3, arb_uni_m, eth_wm

from sqlalchemy.orm import selectinload

async def get_users_with_active_trades(db):
    async with db.AsyncSession() as session:
        result = await session.execute(
            select(User)
            .options(selectinload(User.settings), selectinload(User.active_trades))
            .join(ActiveTrades, ActiveTrades.user_id == User.id)
            .join(UserSetting, UserSetting.user_id == User.id)
            .where(UserSetting.auto_sell == True)
        )
        users = result.scalars().all()
        return users

async def monitor_active_trades():
    while True:
        users = await get_users_with_active_trades(db)
        for user in users:
            for trade in user.active_trades:
                # Check the current price for the token in the trade
                current_price = await get_current_price(trade)

                # Calculate the PNL
                pnl = calculate_pnl(trade)

                # Check if the trade should be sold based on user settings and PNL
                if should_sell_trade(user.settings, pnl):
                    await sell_trade(user, trade)

        # Wait for some time before checking again
        await asyncio.sleep(60)

async def get_current_price(trade):
    # TODO: Implement this function to fetch the current price of the token
    pass

def calculate_pnl(trade):
    # TODO: Implement this function to calculate the PNL based on the amount, purchase price, and current price
    pass

def should_sell_trade(settings, pnl):
    # TODO: Implement this function to determine if the trade should be sold based on user settings and PNL
    pass

async def sell_trade(user, trade):
    # TODO: Implement this function to sell the trade
    pass

async def main():
    await db.connect()
    await monitor_active_trades()

if __name__ == "__main__":
    asyncio.run(main())
