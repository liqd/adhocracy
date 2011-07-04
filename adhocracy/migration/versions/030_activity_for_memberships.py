from datetime import datetime

from sqlalchemy import Table, Column, ForeignKey, MetaData
from sqlalchemy import Boolean, DateTime, Float, Integer

metadata = MetaData()

membership_table_old = Table(
    'membership', metadata,
    Column('id', Integer, primary_key=True),
    Column('approved', Boolean, nullable=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('expire_time', DateTime, nullable=True),
    Column('access_time', DateTime, default=datetime.utcnow,
           onupdate=datetime.utcnow),
    Column('user_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('instance_id', Integer, ForeignKey('instance.id'), nullable=True),
    Column('group_id', Integer, ForeignKey('group.id'), nullable=False),
    )


def upgrade(migrate_engine):
    metadata.bind = migrate_engine
    activity = Column('activity', Float, default=0.0, nullable=True)
    activity.create(membership_table_old)


def downgrade(migrate_engine):
    raise NotImplementedError()
