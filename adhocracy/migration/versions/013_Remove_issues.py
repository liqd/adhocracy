from datetime import datetime

from sqlalchemy import *
from migrate import *

meta = MetaData()


delegateable_table = Table('delegateable', meta,
    Column('id', Integer, primary_key=True),
    Column('label', Unicode(255), nullable=False),
    Column('type', String(50)),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('access_time', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
    Column('delete_time', DateTime, nullable=True),
    Column('creator_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('instance_id', Integer, ForeignKey('instance.id'), nullable=False)
    )
    
comment_table = Table('comment', meta,                  
    Column('id', Integer, primary_key=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('delete_time', DateTime, default=None, nullable=True),
    Column('creator_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('topic_id', Integer, ForeignKey('delegateable.id'), nullable=False),
    Column('canonical', Boolean, default=False),
    Column('wiki', Boolean, default=False),
    Column('reply_id', Integer, ForeignKey('comment.id'), nullable=True),
    Column('poll_id', Integer, ForeignKey('poll.id'), nullable=True)
    )

issue_table = Table('issue', meta,
    Column('id', Integer, ForeignKey('delegateable.id'), primary_key=True),
    Column('comment_id', Integer, ForeignKey('comment.id'), nullable=True)
    )

category_graph = Table('category_graph', meta,
    Column('parent_id', Integer, ForeignKey('delegateable.id')),
    Column('child_id', Integer, ForeignKey('delegateable.id'))
    )
    
poll_table = Table('poll', meta,
    Column('id', Integer, primary_key=True),
    Column('begin_time', DateTime, default=datetime.utcnow),
    Column('end_time', DateTime, nullable=True),
    Column('user_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('action', Unicode(50), nullable=False),
    Column('subject', UnicodeText(), nullable=False),
    Column('scope_id', Integer, ForeignKey('delegateable.id'), nullable=False)
    )

def upgrade(migrate_engine):
    meta.bind = migrate_engine
    issue_table.drop()
    for vals in migrate_engine.execute(delegateable_table.select()):
        if vals[2] == 'issue':
            migrate_engine.execute(category_graph.delete(category_graph.c.parent_id==vals[0]))
            migrate_engine.execute(category_graph.delete(category_graph.c.child_id==vals[0]))
            migrate_engine.execute(comment_table.delete(comment_table.c.topic_id==vals[0]))
            migrate_engine.execute(poll_table.delete(poll_table.c.scope_id==vals[0]))
            migrate_engine.execute(delegateable_table.delete(delegateable_table.c.id==vals[0]))
            

def downgrade(migrate_engine):
    raise NotImplementedError()
