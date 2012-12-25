from datetime import datetime

from sqlalchemy import MetaData, Column, ForeignKey, Table
from sqlalchemy import Boolean, DateTime, Integer, Unicode

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
    #Column('badge_delegateable', Boolean, default=False)
    )

delegateable_badge_table = Table(
    'delegateable_badges', metadata,
    Column('id', Integer, primary_key=True),
    Column('badge_id', Integer, ForeignKey('badge.id'),
           nullable=False),
    Column('delegateable_id', Integer, ForeignKey('delegateable.id'),
           nullable=False),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('creator_id', Integer, ForeignKey('user.id'), nullable=False))
 
def upgrade(migrate_engine):
    metadata.bind = migrate_engine

    #setup
    group_table = Table('group', metadata, autoload=True)
    user_table = Table('user', metadata, autoload=True)
    proposal_table = Table('proposal', metadata, autoload=True)
    delegateable_table = Table('delegateable', metadata, autoload=True)

    #add column badge_delegateable to badge_table
    badge_delegateable = Column('badge_delegateable', Boolean, default=False)
    badge_delegateable.create(badge_table)

    #add new table delegateable_badge
    delegateable_badge_table.create()


def downgrade(migrate_engine):
    raise NotImplementedError()     
