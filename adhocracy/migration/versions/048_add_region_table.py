from sqlalchemy import Column, ForeignKey, MetaData, Table, Index
from sqlalchemy import Integer, Unicode
from geoalchemy import GeometryExtensionColumn, Geometry

meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    instance_table = Table('instance', meta, autoload=True)

    region_table = Table('region', meta,
        Column('id', Integer, primary_key=True),
        Column('name', Unicode(255), nullable=False, index=True),
        Column('admin_level', Integer, nullable=False, index=True),
        Column('admin_type', Unicode(64), nullable=False),
        GeometryExtensionColumn('boundary', Geometry, nullable=False)
    )

    region_table.create()
    region_col = Column('region_id', Integer, ForeignKey('region.id'),
                        nullable=True)
    region_col.create(instance_table)

    boundary_idx = Index('boundary_idx', instance_table.c.boundary,
                         postgresql_using='gist')
    boundary_idx.create()

    #u = instance_table.update(values={'region_id': Null})
    #migrate_engine.execute(u)


def downgrade(migrate_engine):
    raise NotImplementedError()
