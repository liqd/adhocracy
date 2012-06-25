from sqlalchemy import Table, Column, ForeignKey, func, or_, MetaData
from sqlalchemy import DateTime, Integer, Float, Boolean, Unicode, UnicodeText
from geoalchemy import GeometryExtensionColumn, Geometry

meta = MetaData()


instance_table = Table('instance', meta,
    Column('id', Integer, primary_key=True),
    Column('key', Unicode(20), nullable=False, unique=True),
    Column('label', Unicode(255), nullable=False),
    Column('description', UnicodeText(), nullable=True),
    Column('required_majority', Float, nullable=False),
    Column('activation_delay', Integer, nullable=False),
    Column('create_time', DateTime, default=func.now()),
    Column('access_time', DateTime, default=func.now(), onupdate=func.now()),
    Column('delete_time', DateTime, nullable=True),
    Column('creator_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('default_group_id', Integer, ForeignKey('group.id'), nullable=True),
    Column('allow_adopt', Boolean, default=True),
    Column('allow_delegate', Boolean, default=True),
    Column('allow_propose', Boolean, default=True),
    Column('allow_index', Boolean, default=True),
    Column('hidden', Boolean, default=False),
    Column('locale', Unicode(7), nullable=True),
    Column('css', UnicodeText(), nullable=True),
    Column('frozen', Boolean, default=False),
    Column('milestones', Boolean, default=False),
    Column('use_norms', Boolean, nullable=True, default=True),
    Column('require_selection', Boolean, nullable=True, default=False),
    Column('region_id', Integer, ForeignKey('region.id'), nullable=True),
    Column('is_authenticated', Boolean, nullable=True, default=False),
    GeometryExtensionColumn('geo_centre', Geometry, nullable=True)
    )


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    geo_centre_column = GeometryExtensionColumn('geo_centre', Geometry, nullable=True)
    geo_centre_column.create(instance_table)

    geo_centre_idx = Index('geo_centre_idx', instance_table.c.geo_centre, postgresql_using='gist')
    geo_centre_idx.create()


def downgrade(migrate_engine):
    raise NotImplementedError()
