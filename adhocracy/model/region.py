from sqlalchemy import Table, Column, ForeignKey, Index
from sqlalchemy import Float, Integer, Unicode
from geoalchemy import GeometryExtensionColumn, Geometry

from adhocracy.lib.geo import normalize_region_name
from adhocracy.model import meta


region_table = Table(
    'region', meta.data,

    # id corresponds to the osm_id
    Column('id', Integer, primary_key=True),
    Column('name', Unicode(255), nullable=False, index=True),
    Column('admin_level', Integer, nullable=False, index=True),
    Column('admin_type', Unicode(64), nullable=False),
    GeometryExtensionColumn(
        'boundary', Geometry(dimension=2, srid=900913), nullable=False),
    # potentially to be done:
    # de:regionalschluessel (12 stellen, numerisch)
)

Index('boundary_idx', region_table.c.boundary, postgresql_using='gist')


class Region(object):

    __tablename__ = 'region'

    def __init__(self, name, admin_level, admin_type, boundary):
        self.name = name
        self.admin_level = admin_level
        self.admin_type = admin_type
        self.boundary = boundary

    def __repr__(self):
        return u"<Region(%s, admin_level %d)>" % (
            normalize_region_name(self.name), self.admin_level)


region_simplified_table = Table(
    'region_simplified', meta.data,

    Column('id', Integer, primary_key=True),
    Column('region_id', Integer, ForeignKey('region.id'), nullable=False),
    Column('tolerance', Float, nullable=False),
    GeometryExtensionColumn('boundary', Geometry, nullable=False)
)


class RegionSimplified(object):

    __tablename__ = 'region_simplified'

    def __init__(self, region_id, tolerance, boundary):
        self.region_id = region_id
        self.tolerance = tolerance
        self.boundary = boundary


region_hierarchy_table = Table(
    'region_hierarchy', meta.data,

    Column('id', Integer, primary_key=True),
    Column('inner_id', Integer, ForeignKey('region.id'), nullable=False),
    Column('outer_id', Integer, ForeignKey('region.id'), nullable=False),
)


class RegionHierarchy(object):

    __tablename__ = 'region_hierarchy'

    def __init__(self, inner_id, outer_id):
        self.inner_id = inner_id
        self.outer_id = outer_id
