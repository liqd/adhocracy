from datetime import datetime
from pprint import pprint 

from sqlalchemy import *
from migrate import *
import migrate.changeset

import adhocracy.lib.text as text

meta = MetaData()

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

group_table = Table('group', meta, 
    Column('id', Integer, primary_key=True),
    Column('group_name', Unicode(255), nullable=False, unique=True),
    Column('code', Unicode(255), nullable=False, unique=True),
    Column('description', Unicode(1000))
    )

def upgrade(migrate_engine):
    meta.bind = migrate_engine
    instance_table = Table('instance', meta,
        Column('id', Integer, primary_key=True),
        Column('key', Unicode(20), nullable=False, unique=True),
        Column('label', Unicode(255), nullable=False),
        Column('description', UnicodeText(), nullable=True),
        Column('required_majority', Float, nullable=False),
        Column('activation_delay', Integer, nullable=False),
        Column('create_time', DateTime, default=func.now()),
        Column('access_time', DateTime, default=func.now(), onupdate=func.now()),
        Column('delete_time', DateTime, nullable=True),
        Column('creator_id', Integer, ForeignKey('user.id'), nullable=False),
        Column('default_group_id', Integer, ForeignKey('group.id'), nullable=True),
        Column('allow_adopt', Boolean, default=True),       
        Column('allow_delegate', Boolean, default=True),
        Column('allow_index', Boolean, default=True),
        Column('hidden', Boolean, default=False)   
        )
    locale = Column('locale', Unicode(7), nullable=True)
    locale.create(instance_table)

def downgrade(migrate_engine):
    raise NotImplementedError()