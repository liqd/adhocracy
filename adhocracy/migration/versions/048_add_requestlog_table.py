from datetime import datetime

from sqlalchemy import MetaData, Column, Table
from sqlalchemy import DateTime, Integer, Unicode, UnicodeText

meta = MetaData()

requestlog_table = Table('requestlog', meta,
    Column('id', Integer, primary_key=True),
    Column('access_time', DateTime, default=datetime.utcnow),
    Column('ip_address', Unicode(255), nullable=True),
    Column('request_url', UnicodeText()),
    Column('cookies', UnicodeText(), nullable=True),
    Column('user_agent', UnicodeText(), nullable=True),
)

def upgrade(migrate_engine):
    meta.bind = migrate_engine
    requestlog_table.create()

def downgrade(migrate_engine):
    raise NotImplementedError()
