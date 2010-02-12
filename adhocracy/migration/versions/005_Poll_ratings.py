from datetime import datetime

from sqlalchemy import *
from migrate import *
import migrate.changeset

meta = MetaData(migrate_engine)

poll_table = Table('poll', meta,
    Column('id', Integer, primary_key=True),
    Column('begin_time', DateTime, default=datetime.utcnow),
    Column('end_time', DateTime, nullable=True),
    Column('user_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('action', Unicode(50), nullable=False),
    Column('subject', UnicodeText(), nullable=False),
    Column('scope_id', Integer, ForeignKey('delegateable.id'), nullable=False)
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

def upgrade():
    proposal_table = Table('proposal', meta,
        Column('id', Integer, ForeignKey('delegateable.id'), primary_key=True),
        Column('comment_id', Integer, ForeignKey('comment.id'), nullable=True)
        )
    
    rate_poll_id = Column('rate_poll_id', Integer, ForeignKey('poll.id'), nullable=True)
    rate_poll_id.create(proposal_table)
    
    for vals in migrate_engine.execute(proposal_table.select()):
        proposal_id = vals[0]
        q = poll_table.insert(values={'scope': proposal_id, 
                                      'action': u'rate',
                                      'subject': u"@[proposal:%s]" % proposal_id,
                                      'user_id': 1,
                                      'begin_time': datetime.utcnow()})
        r = migrate_engine.execute(q)
        poll_id = r.last_inserted_ids()[-1]
        q = tally_table.insert(values={'create_time': datetime.utcnow(),
                                       'poll_id': poll_id,
                                       'num_for': 0,
                                       'num_against': 0,
                                       'num_abstain': 0})
        r = migrate_engine.execute(q)
    

def downgrade():
    proposal_table = Table('proposal', meta,
        Column('id', Integer, ForeignKey('delegateable.id'), primary_key=True),
        Column('comment_id', Integer, ForeignKey('comment.id'), nullable=True),
        Column('rate_poll_id', Integer, ForeignKey('poll.id'), nullable=True)
        )
    
    proposal_table.c.rate_poll_id.drop()
