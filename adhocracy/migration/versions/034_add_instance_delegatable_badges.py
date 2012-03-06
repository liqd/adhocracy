from datetime import datetime

from sqlalchemy import MetaData, Column, ForeignKey, Table
from sqlalchemy import Boolean, DateTime, Integer, Unicode

metadata = MetaData()

badge_table = Table(
    'badge', metadata,
    #common attributes
    Column('id', Integer, primary_key=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('title', Unicode(40), nullable=False),
    Column('color', Unicode(7), nullable=False),
    Column('description', Unicode(255), default=u'', nullable=False),
    #badges for groups/users
    Column('group_id', Integer, ForeignKey('group.id', ondelete="CASCADE")),
    Column('display_group', Boolean, default=False),
    #badges for delegateables
    Column('badge_delegateable', Boolean, default=False),
    #badges only for delegateables inside an instance (aka "category")
    #Column('badge_delegateable_category', Boolean, default=False),
    #Column('instance_id', Integer, ForeignKey('instance.id'), nullable=True))
    )


def upgrade(migrate_engine):
    metadata.bind = migrate_engine

    #setup
    group_table = Table('group', metadata, autoload=True)
    user_table = Table('user', metadata, autoload=True)
    proposal_table = Table('proposal', metadata, autoload=True)
    intance_table = Table('instance', metadata, autoload=True)

    #add new columns to badge_table
    badge_instance_delegateable = Column('badge_delegateable_category', Boolean, default=False)
    badge_instance_delegateable.create(badge_table)
    badge_instance_id = Column('instance_id', Integer, ForeignKey('instance.id'), nullable=True)
    badge_instance_id.create(badge_table)


def downgrade(migrate_engine):
    raise NotImplementedError()
