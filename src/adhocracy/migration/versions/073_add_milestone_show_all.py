from sqlalchemy import MetaData, Table, Column
from sqlalchemy import Boolean


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)

    table = Table('milestone', meta, autoload=True)
    col = Column('show_all_proposals', Boolean, default=False)
    col.create(table)
