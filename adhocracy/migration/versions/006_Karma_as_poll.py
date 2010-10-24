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

karma_table = Table('karma', meta,
    Column('id', Integer, primary_key=True),
    Column('value', Integer, nullable=False),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('comment_id', Integer, ForeignKey('comment.id'), nullable=False),
    Column('donor_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('recipient_id', Integer, ForeignKey('user.id'), nullable=False),   
    )

vote_table = Table('vote', meta, 
    Column('id', Integer, primary_key=True),
    Column('orientation', Integer, nullable=False),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('user_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('poll_id', Integer, ForeignKey('poll.id'), nullable=False),
    Column('delegation_id', Integer, ForeignKey('delegation.id'), nullable=True)
    )

user_table = Table('user', meta,
    Column('id', Integer, primary_key=True),
    Column('user_name', Unicode(255), nullable=False, unique=True, index=True),
    Column('display_name', Unicode(255), nullable=True, index=True),
    Column('bio', UnicodeText(), nullable=True),
    Column('email', Unicode(255), nullable=True, unique=False),
    Column('email_priority', Integer, default=3),
    Column('activation_code', Unicode(255), nullable=True, unique=False),
    Column('reset_code', Unicode(255), nullable=True, unique=False),
    Column('password', Unicode(80), nullable=False),
    Column('locale', Unicode(7), nullable=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('access_time', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
    Column('delete_time', DateTime)
    )

def upgrade(migrate_engine):
    meta.bind = migrate_engine
    comment_table = Table('comment', meta,                  
        Column('id', Integer, primary_key=True),
        Column('create_time', DateTime, default=datetime.utcnow),
        Column('delete_time', DateTime, default=None, nullable=True),
        Column('creator_id', Integer, ForeignKey('user.id'), nullable=False),
        Column('topic_id', Integer, ForeignKey('delegateable.id'), nullable=False),
        Column('canonical', Boolean, default=False),
        Column('reply_id', Integer, ForeignKey('comment.id'), nullable=True)
        )
    
    poll_id = Column('poll_id', Integer, ForeignKey('poll.id'), nullable=True)
    poll_id.create(comment_table)
    
    q = migrate_engine.execute(comment_table.select())
    for (comment_id, create_time, 
         delete_time, creator_id, 
         topic_id, _, _, _) in q:
        
        q = poll_table.insert(values={'scope_id': topic_id, 
                                      'action': u'rate',
                                      'subject': u"@[comment:%s]" % comment_id,
                                      'user_id': creator_id,
                                      'begin_time': create_time,
                                      'end_time': delete_time})
        r = migrate_engine.execute(q)
        poll_id = r.last_inserted_ids()[-1]
        z = tally_table.insert(values={'create_time': create_time,
                                       'poll_id': poll_id,
                                       'num_for': 0,
                                       'num_against': 0,
                                       'num_abstain': 0})
        r = migrate_engine.execute(z)
        
        a = migrate_engine.execute(karma_table.select(karma_table.c.comment_id==comment_id))
        for (_, value, k_time, _, donor_id, _) in a:
            y = vote_table.insert(values={'create_time': k_time,
                                          'poll_id': poll_id,                             
                                          'user_id': donor_id,
                                          'orientation': value})
            r = migrate_engine.execute(y)
        
        u = comment_table.update(comment_table.c.id==comment_id, values={
            'poll_id': poll_id
            })
        migrate_engine.execute(u)
    
    karma_table.drop()

def downgrade(migrate_engine):
    raise NotImplementedError()
