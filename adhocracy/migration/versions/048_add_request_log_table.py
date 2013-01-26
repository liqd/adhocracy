from datetime import datetime

from sqlalchemy import MetaData, Column, Table
from sqlalchemy import Boolean, DateTime, Integer, Unicode, UnicodeText

meta = MetaData()

request_table = Table('request', meta,
    Column('id', Integer, primary_key=True),
    Column('cookies', UnicodeText()),
    Column('remote_ip_address', Unicode(255)),
    Column('useragent', UnicodeText()),
    Column('request_url', UnicodeText()),
    Column('proxy', UnicodeText()),
    Column('access_time', DateTime, default=datetime.utcnow),
    )

def upgrade(migrate_engine):
    meta.bind = migrate_engine
    request_table.create()

def downgrade(migrate_engine):
    raise NotImplementedError()
