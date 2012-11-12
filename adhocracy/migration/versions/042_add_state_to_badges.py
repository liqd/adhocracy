from datetime import datetime

from sqlalchemy import MetaData
from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy import Boolean, DateTime, Integer, Unicode, String

metadata = MetaData()

badge_table = Table(
    'badge', metadata,
    Column('id', Integer, primary_key=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('title', Unicode(40), nullable=False),
    Column('color', Unicode(7), nullable=False),
    Column('description', Unicode(255), default=u'', nullable=False),
    Column('group_id', Integer, ForeignKey('group.id', ondelete="CASCADE")),
    Column('display_group', Boolean, default=False),
    Column('badge_delegateable', Boolean, default=False)
    #Column('state'), String(30), default="invisible")
    )


def upgrade(migrate_engine):
    metadata.bind = migrate_engine

    #setup
    group_table = Table('group', metadata, autoload=True)

    #add column badge_delegateable to badge_table
    badge_state = Column('state', String(30), default="visible")
    badge_state.create(badge_table)


def downgrade(migrate_engine):
    raise NotImplementedError()
