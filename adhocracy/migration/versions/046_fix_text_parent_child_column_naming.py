from datetime import datetime
from sqlalchemy import Column, ForeignKey, MetaData, Table
from sqlalchemy import Boolean, DateTime, Integer, Unicode, UnicodeText

metadata = MetaData()

user_table = Table('user', metadata,
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
    Column('access_time', DateTime, default=datetime.utcnow,
           onupdate=datetime.utcnow),
    Column('delete_time', DateTime),
    Column('banned', Boolean, default=False),
    Column('no_help', Boolean, default=False, nullable=True),
    Column('page_size', Integer, default=10, nullable=True),
    Column('proposal_sort_order', Unicode(50), default=None, nullable=True)
    )

page_table = Table('page', metadata,
    Column('id', Integer, ForeignKey('delegateable.id'), primary_key=True),
    Column('function', Unicode(20))
    )


def upgrade(migrate_engine):
    metadata.bind = migrate_engine
    text_table = Table('text', metadata,
        Column('id', Integer, primary_key=True),
        Column('page_id', Integer, ForeignKey('page.id'), nullable=False),
        Column('user_id', Integer, ForeignKey('user.id'), nullable=False),
        Column('parent_id', Integer, ForeignKey('text.id'), nullable=True),
        Column('variant', Unicode(255), nullable=True),
        Column('title', Unicode(255), nullable=True),
        Column('text', UnicodeText(), nullable=True),
        Column('wiki', Boolean, default=False),
        Column('create_time', DateTime, default=datetime.utcnow),
        Column('delete_time', DateTime)
        )

    text_table.c.parent_id.alter(name='child_id')


def downgrade(migrate_engine):
    raise NotImplementedError()
