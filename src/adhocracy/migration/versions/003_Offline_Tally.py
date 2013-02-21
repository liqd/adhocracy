from datetime import datetime

from sqlalchemy import *
from migrate import *

meta = MetaData()

poll_table = Table('poll', meta,
    Column('id', Integer, primary_key=True),
    Column('begin_time', DateTime, default=datetime.utcnow),
    Column('end_time', DateTime, nullable=True),
    Column('begin_user_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('proposal_id', Integer, ForeignKey('proposal.id'), nullable=False)   
    )

vote_table = Table('vote', meta, 
    Column('id', Integer, primary_key=True),
    Column('orientation', Integer, nullable=False),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('user_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('poll_id', Integer, ForeignKey('poll.id'), nullable=False),
    Column('delegation_id', Integer, ForeignKey('delegation.id'), nullable=True)
    )

tally_table = Table('tally', meta,
    Column('id', Integer, primary_key=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('poll_id', Integer, ForeignKey('poll.id'), nullable=False),
    Column('vote_id', Integer, ForeignKey('vote.id'), nullable=True),
    Column('num_for', Integer, nullable=True),
    Column('num_against', Integer, nullable=True),
    Column('num_abstain', Integer, nullable=True)
    )

def upgrade(migrate_engine):
    meta.bind = migrate_engine
    tally_table.create()

def downgrade(migrate_engine):
    raise NotImplementedError()
