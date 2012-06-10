from sqlalchemy import (MetaData, Column, ForeignKey, Boolean, DateTime,
                        Integer, PickleType, Table)
from geoalchemy import GeometryExtensionColumn, Geometry

metadata = MetaData()


proposal_table = Table('proposal', metadata,
    Column('id', Integer, ForeignKey('delegateable.id'), primary_key=True),
    Column('description_id', Integer, ForeignKey('page.id'), nullable=True),
    Column('adopt_poll_id', Integer, ForeignKey('poll.id'), nullable=True),
    Column('rate_poll_id', Integer, ForeignKey('poll.id'), nullable=True),
    Column('adopted', Boolean, default=False),
    )


def upgrade(migrate_engine):
    metadata.bind = migrate_engine

    geotag_column = GeometryExtensionColumn('geotag', Geometry, nullable=True)
    geotag_column.create(proposal_table)


def downgrade(migrate_engine):
    raise NotImplementedError()
