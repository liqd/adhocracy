from sqlalchemy import Column, ForeignKey, MetaData, Table, Float
from sqlalchemy import Integer
from geoalchemy import GeometryExtensionColumn, Geometry

meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    region_table = Table('region', meta, autoload=True)

    region_simplified_table = Table('region_simplified', meta,
        Column('id', Integer, primary_key=True),
        Column('region_id', Integer, ForeignKey('region.id'), nullable=False),
        Column('tolerance', Float, nullable=False),
        GeometryExtensionColumn('boundary', Geometry, nullable=False)
    )

    region_simplified_table.create()


def downgrade(migrate_engine):
    raise NotImplementedError()
