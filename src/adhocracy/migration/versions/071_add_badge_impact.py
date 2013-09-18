from sqlalchemy import MetaData, Table, Column
from sqlalchemy import Integer


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)

    table = Table('badge', meta, autoload=True)
    col = Column('impact', Integer, default=0, server_default=u'0',
                 nullable=False)
    col.create(table)
