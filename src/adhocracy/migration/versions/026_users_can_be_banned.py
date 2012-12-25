from datetime import datetime
from sqlalchemy import Column, ForeignKey, MetaData, Table
from sqlalchemy import Boolean, DateTime, Integer, Unicode, UnicodeText

meta = MetaData()


group_table = Table('group', meta)


page_table = Table('page', meta)


def upgrade(migrate_engine):
    meta.bind = migrate_engine
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
        Column('access_time', DateTime, default=datetime.utcnow,
               onupdate=datetime.utcnow),
        Column('delete_time', DateTime),
        Column('no_help', Boolean, default=False, nullable=True),
        Column('page_size', Integer, default=10, nullable=True)
        )
    banned = Column('banned', Boolean, default=False)
    banned.create(user_table)
    u = user_table.update(values={'banned': False})
    migrate_engine.execute(u)


def downgrade(migrate_engine):
    raise NotImplementedError()

