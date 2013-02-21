from datetime import datetime

from sqlalchemy import *
from migrate import *
import migrate.changeset

meta = MetaData(migrate_engine)

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
    comment_table = Table('comment', meta,                  
        Column('id', Integer, primary_key=True),
        Column('create_time', DateTime, default=datetime.utcnow),
        Column('delete_time', DateTime, default=None, nullable=True),
        Column('creator_id', Integer, ForeignKey('user.id'), nullable=False),
        Column('topic_id', Integer, ForeignKey('delegateable.id'), nullable=False),
        Column('canonical', Boolean, default=False),
        Column('reply_id', Integer, ForeignKey('comment.id'), nullable=True),
        Column('poll_id', Integer, ForeignKey('poll.id'), nullable=True)
        )
    wiki = Column('wiki', Boolean, default=False)
    wiki.create(comment_table)
    u = comment_table.update(values={
        'wiki': True
        })
    migrate_engine.execute(u)
    

def downgrade(migrate_engine):
    raise NotImplementedError()
