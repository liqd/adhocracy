from sqlalchemy import MetaData, Column, Table
from sqlalchemy import Unicode, UnicodeText

metadata = MetaData()

staticpage_table = Table(
    'staticpage', metadata,
    Column('key', Unicode(256), primary_key=True),
    Column('lang', Unicode(7), primary_key=True),
    Column('title', UnicodeText(), nullable=True),
    Column('body', UnicodeText()),
)


def upgrade(migrate_engine):
    metadata.bind = migrate_engine
    staticpage_table.create()


def downgrade(migrate_engine):
    raise NotImplementedError()
