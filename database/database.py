from sqlalchemy import create_engine

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine
from contextlib import asynccontextmanager
from database.client import Client
from bot.utils.config import DBUSER, DBPASS, DBHOST, DBNAME
Base = declarative_base()


# # Replace the following values with your MySQL configuration
# user = 'root'
# password = 'testDB77!!'
# host = 'localhost'
# db_name = 'SniperDB'

def get_db():
    db = Client(username=DBUSER,
            password=DBPASS,
            host=DBHOST,
            name=DBNAME)
    return db


# CREATE USER 'yasir'@'localhost' IDENTIFIED BY 'testpw12345';
# GRANT ALL PRIVILEGES ON SniperDB.* TO 'yasir'@'localhost';
