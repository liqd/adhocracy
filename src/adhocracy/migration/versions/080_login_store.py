from datetime import datetime
from sqlalchemy import MetaData, Table, Boolean, Column
from sqlalchemy import Integer, DateTime, Unicode, UnicodeText

meta = MetaData()

login_table = Table(
    'loginlog', meta,
    Column('access_time', DateTime, default=datetime.utcnow),
    Column('ip_address', Unicode(255), nullable=True),
    Column('user', UnicodeText()),
    Column('success', UnicodeText())
)


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    login_table.create()
