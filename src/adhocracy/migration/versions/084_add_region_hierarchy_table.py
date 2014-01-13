from sqlalchemy import Column, ForeignKey, MetaData, Table
from sqlalchemy import Integer

meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    region_table = Table('region', meta, autoload=True)

    region_hierarchy_table = Table('region_hierarchy', meta,
        Column('id', Integer, primary_key=True),
        Column('inner_id', Integer, ForeignKey('region.id'), nullable=False),
        Column('outer_id', Integer, ForeignKey('region.id'), nullable=False),
    )

    region_hierarchy_table.create()


def downgrade(migrate_engine):
    raise NotImplementedError()
