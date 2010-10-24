from datetime import datetime
from pprint import pprint 

from sqlalchemy import *
from migrate import *
import migrate.changeset

import adhocracy.lib.text as text

meta = MetaData()

user_table = Table('user', meta)

group_table = Table('group', meta)
    
delegateable_table = Table('delegateable', meta)
    
page_table = Table('page', meta)

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
        Column('hidden', Boolean, default=False),
        Column('locale', Unicode(7), nullable=True),
        Column('css', UnicodeText(), nullable=True)
        )
    use_norms = Column('use_norms', Boolean, nullable=True, default=True)
    use_norms.create(instance_table)
    u = instance_table.update(values={
        'use_norms': True
        })
    migrate_engine.execute(u)

def downgrade(migrate_engine):
    raise NotImplementedError()
