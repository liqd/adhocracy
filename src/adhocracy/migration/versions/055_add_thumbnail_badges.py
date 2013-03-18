from datetime import datetime
from sqlalchemy import Column, ForeignKey, MetaData, Table
from sqlalchemy import (Boolean, Integer, DateTime, String, Unicode,
                        LargeBinary)

metadata = MetaData()

#table to update
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
    Column('visible', Boolean, default=True),
    extend_existing=True
)


def upgrade(migrate_engine):
    #use sqlalchemy-migrate database connection
    metadata.bind = migrate_engine
    #autoload needed tables
    instance_table = Table('instance', metadata, autoload=True)
    #add thumbnail column to table
    thumbnail = Column('thumbnail', LargeBinary, default=None, nullable=True)
    #create/recreate the table
    thumbnail.create(badge_table)


def downgrade(migrate_engine):
    raise NotImplementedError()
