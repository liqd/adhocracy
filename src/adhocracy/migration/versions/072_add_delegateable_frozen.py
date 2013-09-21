from sqlalchemy import MetaData, Table, Column
from sqlalchemy import Boolean


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)

    table = Table('delegateable', meta, autoload=True)
    col = Column('frozen', Boolean, default=False)
    col.create(table)
