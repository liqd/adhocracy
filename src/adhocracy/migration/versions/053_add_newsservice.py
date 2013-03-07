from datetime import datetime

from sqlalchemy import MetaData, Column, ForeignKey, Table
from sqlalchemy import Boolean, DateTime, Integer, Unicode, UnicodeText

metadata = MetaData()

message_table = Table(
    'message', metadata,
    Column('id', Integer, primary_key=True),
    Column('subject', Unicode(140), nullable=False),
    Column('body', UnicodeText(), nullable=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('access_time', DateTime, default=datetime.utcnow,
           onupdate=datetime.utcnow),
    Column('delete_time', DateTime, nullable=True),
    Column('creator_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('sender_email', Unicode(255), nullable=False),
)

message_recipient_table = Table(
    'message_recipient', metadata,
    Column('id', Integer, primary_key=True),
    Column('message_id', Integer, ForeignKey('message.id'), nullable=False),
    Column('recipient_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('email_sent', Boolean, default=False),
)

user_table = Table(
    'user', metadata,
    Column('id', Integer, primary_key=True),
    Column('user_name', Unicode(255), nullable=False, unique=True, index=True),
    Column('display_name', Unicode(255), nullable=True, index=True),
    Column('bio', UnicodeText(), nullable=True),
    Column('email', Unicode(255), nullable=True, unique=True),
    Column('email_priority', Integer, default=3),
    Column('activation_code', Unicode(255), nullable=True, unique=False),
    Column('reset_code', Unicode(255), nullable=True, unique=False),
    Column('password', Unicode(80), nullable=False),
    Column('locale', Unicode(7), nullable=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('access_time', DateTime, default=datetime.utcnow,
           onupdate=datetime.utcnow),
    Column('delete_time', DateTime),
    Column('banned', Boolean, default=False),
    Column('no_help', Boolean, default=False, nullable=True),
    Column('page_size', Integer, default=10, nullable=True),
    Column('proposal_sort_order', Unicode(50), default=None, nullable=True),
    Column('gender', Unicode(1), default=None),
)


def upgrade(migrate_engine):
    metadata.bind = migrate_engine
    message_table.create()
    message_recipient_table.create()

    email_messages = Column('email_messages', Boolean, default=True)
    email_messages.create(user_table)


def downgrade(migrate_engine):
    raise NotImplementedError()
