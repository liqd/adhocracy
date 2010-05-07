from datetime import datetime
from pprint import pprint 

from sqlalchemy import *
from migrate import *
import migrate.changeset

import adhocracy.lib.text as text

meta = MetaData(migrate_engine)

def upgrade():
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
        
    variant = Column('variant', Unicode(255), nullable=True)
    variant.create(comment_table)
        
    u = comment_table.update(values={
        'variant': u'HEAD'
        })
    migrate_engine.execute(u)

def downgrade():
    comment_table = Table('comment', meta,                  
        Column('id', Integer, primary_key=True),
        Column('create_time', DateTime, default=datetime.utcnow),
        Column('delete_time', DateTime, default=None, nullable=True),
        Column('creator_id', Integer, ForeignKey('user.id'), nullable=False),
        Column('topic_id', Integer, ForeignKey('delegateable.id'), nullable=False),
        Column('canonical', Boolean, default=False),
        Column('wiki', Boolean, default=False),
        Column('reply_id', Integer, ForeignKey('comment.id'), nullable=True),
        Column('poll_id', Integer, ForeignKey('poll.id'), nullable=True),
        Column('variant', Unicode(255), nullable=True)
        )
    comment_table.c.variant.drop()