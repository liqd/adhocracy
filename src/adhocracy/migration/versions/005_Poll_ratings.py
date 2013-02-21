from datetime import datetime

from sqlalchemy import *
from migrate import *
import migrate.changeset

meta = MetaData()

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
    
def upgrade(migrate_engine):
    meta.bind = migrate_engine
    proposal_table = Table('proposal', meta,
        Column('id', Integer, ForeignKey('delegateable.id'), primary_key=True),
        Column('comment_id', Integer, ForeignKey('comment.id'), nullable=True)
        )
    
    rate_poll_id = Column('rate_poll_id', Integer, ForeignKey('poll.id'), nullable=True)
    rate_poll_id.create(proposal_table)
    
    for vals in migrate_engine.execute(proposal_table.select()):
        proposal_id = vals[0]
        q = poll_table.insert(values={'scope_id': proposal_id, 
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
        q = proposal_table.update(proposal_table.c.id==proposal_id,
                                  {'rate_poll_id': poll_id})
        migrate_engine.execute(q)
    
def downgrade(migrate_engine):
    raise NotImplementedError()
