from sqlalchemy import MetaData, Column, Table
from sqlalchemy import Integer, Unicode, UnicodeText

meta = MetaData()

request_table = Table('request', meta,
    Column('id', Integer, primary_key=True),
    Column('cookies', UnicodeText()),
    Column('remote_ip_address', Unicode(255)),
    Column('useragent', UnicodeText()),
    Column('request_url', UnicodeText()),
    Column('proxy', UnicodeText()),
    )

def upgrade(migrate_engine):
    meta.bind = migrate_engine
    request_table.create()

def downgrade(migrate_engine):
    raise NotImplementedError()
