from sqlalchemy import MetaData, Table, Unicode, Column


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)

    table = Table('message', meta, autoload=True)
    col = Column('sender_name', Unicode(255), nullable=True)
    col.create(table)
