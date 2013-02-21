from datetime import datetime
from pprint import pprint 

from sqlalchemy import *
from migrate import *
import migrate.changeset

meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine
    user_table = Table('user', meta,
        Column('id', Integer, primary_key=True),
        Column('user_name', Unicode(255), nullable=False, unique=True, index=True),
        Column('display_name', Unicode(255), nullable=True, index=True),
        Column('bio', UnicodeText(), nullable=True),
        Column('email', Unicode(255), nullable=True, unique=False),
        Column('email_priority', Integer, default=3),
        Column('activation_code', Unicode(255), nullable=True, unique=False),
        Column('reset_code', Unicode(255), nullable=True, unique=False),
        Column('password', Unicode(80), nullable=False),
        Column('locale', Unicode(7), nullable=True),
        Column('create_time', DateTime, default=datetime.utcnow),
        Column('access_time', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
        Column('delete_time', DateTime)
        )
    no_help = Column('no_help', Boolean, default=False, nullable=True)
    no_help.create(user_table)
    page_size = Column('page_size', Integer, default=10, nullable=True)
    page_size.create(user_table)

def downgrade(migrate_engine):
    raise NotImplementedError()