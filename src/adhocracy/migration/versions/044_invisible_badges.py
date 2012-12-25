from datetime import datetime

from sqlalchemy import MetaData
from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy import Boolean, DateTime, Integer, Unicode, String

metadata = MetaData()

badge_table = Table(
    'badge', metadata,
    #common attributes
    Column('id', Integer, primary_key=True),
    Column('type', String(40), nullable=False),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('title', Unicode(40), nullable=False),
    Column('color', Unicode(7), nullable=False),
    Column('description', Unicode(255), default=u'', nullable=False),
    Column('instance_id', Integer, ForeignKey('instance.id',
                                              ondelete="CASCADE",),
           nullable=True),
    # attributes for UserBadges
    Column('group_id', Integer, ForeignKey('group.id', ondelete="CASCADE")),
    Column('display_group', Boolean, default=False),
    #Column('visible', Boolean, default=True))
    )


def upgrade(migrate_engine):
    metadata.bind = migrate_engine

    badge_state = Column('visible', Boolean, default=True)
    badge_state.create(badge_table)


def downgrade(migrate_engine):
    raise NotImplementedError()