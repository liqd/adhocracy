from sqlalchemy import MetaData, Table

from sqlalchemy.types import TEXT


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)

    table = Table('user', meta, autoload=True)
    col = table.c.optional_attributes
    if col.type != TEXT:
        col.alter(type=TEXT)
