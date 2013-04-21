from sqlalchemy import MetaData, Table, Boolean, Column

from sqlalchemy import Integer


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)

    message_table = Table('message', meta, autoload=True)
    col = Column('include_footer', Boolean, nullable=False, default=True,
                 server_default="1")
    col.create(message_table)
