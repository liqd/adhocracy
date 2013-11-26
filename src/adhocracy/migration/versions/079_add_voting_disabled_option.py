from sqlalchemy import MetaData, Table, Boolean, Column

from sqlalchemy import Integer


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)

    instance_table = Table('instance', meta, autoload=True)
    col = Column('voting_disabled', Boolean, nullable=False, default=False,
                 server_default="0")
    col.create(instance_table)

