from contextlib import suppress

import sqlalchemy.exc
from sqlalchemy import insert

from bot.db_client import db

from sqlalchemy_utils import create_database, drop_database
from sqlalchemy.orm import declarative_base
Base = declarative_base()
def init():
    """
    Create Database and do the
    Initial inserts:
    - punishments
    - roles
    """
    engine = db.engine
    with suppress(sqlalchemy.exc.OperationalError):
        drop_database(db.engine_string())
    create_database(db.engine_string())
    Base.metadata.create_all(bind=engine)

    


def soft_init():
    engine = db.engine
    Base.metadata.create_all(bind=engine)

soft_init()


# things migrated to log channel: user edits, bans, mutes, kicks,
