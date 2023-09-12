from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()
class Client:
    def __init__(
        self,
        username: str,
        password: str,
        host: str,
        name: str
    ) -> None:
        self.username = username
        self.password = password
        self.host = host
        self.name = name
        
        self.engine = create_engine(
            self.engine_string(),
            pool_size=50,
            max_overflow=100
        )

        self.async_engine = create_async_engine(
            self.engine_string(async_engine=True),
            pool_size=50,
            max_overflow=100,
            pool_timeout=299
        )

        self.Session = sessionmaker(bind=self.engine)
        self.AsyncSession = sessionmaker(
            bind=self.async_engine,
            expire_on_commit=False,
            class_=AsyncSession
        )
        Base.metadata.create_all(self.engine)

    def engine_string(self, async_engine: bool = False):
        return "mysql+{}://{}:{}@{}/{}".format(
            "aiomysql" if async_engine else "mysqldb",
            self.username,
            self.password,
            self.host,
            self.name
        )
    def create_tables(self):
        Base.metadata.create_all(self.engine)
