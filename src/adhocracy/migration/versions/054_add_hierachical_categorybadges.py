from datetime import datetime
from sqlalchemy import Column, ForeignKey, MetaData, Table
from sqlalchemy import Boolean, Integer, DateTime, String, Unicode, LargeBinary

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
)


def upgrade(migrate_engine):
    #use sqlalchemy-migrate database connection
    metadata.bind = migrate_engine
    #autoload needed tables
    instance_table = Table('instance', metadata, autoload=True)
    #add hierachical columns to the table
    select_child_desc = Column('select_child_description', Unicode(255), default=u'', nullable=True)
    parent = Column('parent_id', Integer, ForeignKey('badge.id', ondelete="CASCADE"),
                    nullable=True)
    #create/recreate the table
    select_child_desc.create(badge_table)
    select_child_desc.alter(nullable=False)
    parent.create(badge_table)

def downgrade(migrate_engine):
    raise NotImplementedError()
