from sqlalchemy import MetaData, Table, Unicode, Column


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)

    table = Table('badge', meta, autoload=True)
    col = Column('title_f', Unicode(40), nullable=True)
    col.create(table)
    col = Column('title_m', Unicode(40), nullable=True)
    col.create(table)
    col = Column('title_o', Unicode(40), nullable=True)
    col.create(table)
