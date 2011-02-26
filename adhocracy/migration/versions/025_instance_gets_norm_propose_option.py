from datetime import datetime
from sqlalchemy import Column, ForeignKey, MetaData, Table, Float
from sqlalchemy import Boolean, DateTime, Integer, Unicode, UnicodeText
from sqlalchemy import func, or_

meta = MetaData()

user_table = Table('user', meta)
group_table = Table('group', meta)

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
        Column('css', UnicodeText(), nullable=True),
        Column('use_norms', Boolean, nullable=True, default=True)
    )
    
    propose = Column('allow_propose', Boolean, default=True)
    propose.create(instance_table)
    u = instance_table.update(values={'allow_propose': True})
    migrate_engine.execute(u)


def downgrade(migrate_engine):
    raise NotImplementedError()

