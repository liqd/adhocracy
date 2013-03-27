from sqlalchemy import MetaData
from sqlalchemy import Column, ForeignKey, Table, func
from sqlalchemy import Boolean, DateTime, Float, Integer, Unicode, UnicodeText
from geoalchemy import GeometryExtensionColumn, Geometry

metadata = MetaData()

instance_table = Table(
    'instance', metadata,
    Column('id', Integer, primary_key=True),
    Column('key', Unicode(20), nullable=False, unique=True),
    Column('label', Unicode(255), nullable=False),
    Column('description', UnicodeText(), nullable=True),
    Column('required_majority', Float, nullable=False),
    Column('activation_delay', Integer, nullable=False),
    Column('create_time', DateTime, default=func.now()),
    Column('access_time', DateTime, default=func.now(),
           onupdate=func.now()),
    Column('delete_time', DateTime, nullable=True),
    Column('creator_id', Integer, ForeignKey('user.id'),
           nullable=False),
    Column('default_group_id', Integer, ForeignKey('group.id'),
           nullable=True),
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
    Column('is_authenticated', Boolean, nullable=True, default=False),
    Column('hide_global_categories', Boolean, nullable=True, default=False),
    Column('editable_comments_default', Boolean, nullable=True, default=True),
    Column('require_valid_email', Boolean, nullable=True, default=True),
    Column('show_norms_navigation', Boolean, nullable=True, default=True),
    Column('region_id', Integer, ForeignKey('region.id'), nullable=True),
    GeometryExtensionColumn('geo_centre',
                            Geometry(dimension=2, srid=900913),
                            nullable=True),
)


def upgrade(migrate_engine):
    metadata.bind = migrate_engine

    use_maps = Column('use_maps',
                      Boolean,
                      default=True)
    use_maps.create(instance_table)


def downgrade(migrate_engine):
    raise NotImplementedError()
