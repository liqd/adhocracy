from datetime import datetime

from sqlalchemy import *
from migrate import *
import migrate.changeset

meta = MetaData()

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
        Column('allow_adopt', Boolean, default=True)
        )
              
    allow_delegate = Column('allow_delegate', Boolean, default=True)
    allow_delegate.create(instance_table)
    allow_index = Column('allow_index', Boolean, default=True)
    allow_index.create(instance_table)
    hidden = Column('hidden', Boolean, default=False)
    hidden.create(instance_table)


def downgrade(migrate_engine):
    raise NotImplementedError()
