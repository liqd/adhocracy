from sqlalchemy import Table, MetaData
from sqlalchemy import Unicode

metadata = MetaData()


def upgrade(migrate_engine):
    metadata.bind = migrate_engine

    instance_table = Table('instance', metadata, autoload=True)
    key_column = instance_table.c.key

    key_column.alter(type=Unicode(63))


def downgrade(migrate_engine):
    raise NotImplementedError()
