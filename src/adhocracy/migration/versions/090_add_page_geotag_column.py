from sqlalchemy import (MetaData, Column, ForeignKey, Unicode,
                        Integer, Table)
from geoalchemy import GeometryExtensionColumn, Geometry

meta = MetaData()


page_table = Table('page', meta,
    Column('id', Integer, ForeignKey('delegateable.id'), primary_key=True),
    Column('function', Unicode(20)),
    )


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    geotag_column = GeometryExtensionColumn(
        'geotag', Geometry(dimension=2, srid=900913), nullable=True)
    geotag_column.create(page_table)


def downgrade(migrate_engine):
    raise NotImplementedError()
