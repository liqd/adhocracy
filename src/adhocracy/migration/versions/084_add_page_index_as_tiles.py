from sqlalchemy import Column, MetaData, Table
from sqlalchemy import Boolean

metadata = MetaData()


def upgrade(migrate_engine):
    metadata.bind = migrate_engine

    instance_table = Table('instance', metadata, autoload=True)

    page_index_as_tiles = Column('page_index_as_tiles',
                                 Boolean,
                                 nullable=True,
                                 default=False)
    page_index_as_tiles.create(instance_table)


def downgrade(migrate_engine):
    raise NotImplementedError()
