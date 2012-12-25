from datetime import datetime
from pprint import pprint 

from sqlalchemy import *
from migrate import *
import migrate.changeset

meta = MetaData()


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
    Column('delete_time', DateTime),
    Column('no_help', Boolean, default=False, nullable=True),
    Column('page_size', Integer, default=10, nullable=True)
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
    Column('poll_id', Integer, ForeignKey('poll.id'), nullable=True),
    Column('variant', Unicode(255), nullable=True)
    )


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    revision_table = Table('revision', meta,
        Column('id', Integer, primary_key=True),
        Column('create_time', DateTime, default=datetime.utcnow),
        Column('text', UnicodeText(), nullable=False),
        Column('sentiment', Integer, default=0),
        Column('user_id', Integer, ForeignKey('user.id'), nullable=False),
        Column('comment_id', Integer, ForeignKey('comment.id'), nullable=False)
        )
    title = Column('title', Unicode(255), nullable=True)
    title.create(revision_table)

def downgrade(migrate_engine):
    raise NotImplementedError()