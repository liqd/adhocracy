from sqlalchemy import MetaData, Table, Unicode, Column


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)

    table = Table('badge', meta, autoload=True)
    col = Column('behavior_proposal_sort_order', Unicode(50), nullable=True)
    col.create(table)
