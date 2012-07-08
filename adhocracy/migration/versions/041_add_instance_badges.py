from datetime import datetime

from sqlalchemy import MetaData, Column, ForeignKey, Table
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
    Column('display_group', Boolean, default=False))

instance_badges_table = Table(
    'instance_badges', metadata,
    Column('id', Integer, primary_key=True),
    Column('badge_id', Integer, ForeignKey('badge.id'),
           nullable=False),
    Column('instance_id', Integer, ForeignKey('instance.id'),
           nullable=False),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('creator_id', Integer, ForeignKey('user.id'), nullable=False))


def upgrade(migrate_engine):
    metadata.bind = migrate_engine

    #setup
    group_table = Table('group', metadata, autoload=True)
    user_table = Table('user', metadata, autoload=True)
    instance_table = Table('instance', metadata, autoload=True)

    #add new table instance_badge
    instance_badges_table.create()


def downgrade(migrate_engine):
    raise NotImplementedError()
