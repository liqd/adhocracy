from sqlalchemy import Table, Column, ForeignKey, Index
from sqlalchemy import Float, Integer, Text, Unicode
from geoalchemy.geometry import MultiPolygon
from geoalchemy import GeometryExtensionColumn, Geometry

from adhocracy.model import meta


boundary_table = Table('boundary', meta.data,
    # id corresponds to osm_id
    Column('id', Integer, primary_key = True),
    Column('admin_level', Integer, nullable=False, index=True),
    GeometryExtensionColumn('geometry', Geometry(dimension=2, srid=900913), nullable=False)
    )

Index('boundary_geometry_idx', boundary_table.c.geometry, postgresql_using='gist')


class Boundary(object):
    """
    A piece of a boundary. Corresponds to an OSM way with tag
    boundary=administrative.
    """

    __tablename__ = 'boundary'

    def __init__(self, admin_level, geometry):
        self.admin_level = admin_level
        self.geometry = geometry


region_table = Table('region', meta.data,
    # id corresponds to the osm_id
    Column('id', Integer, primary_key = True),
    Column('name', Unicode(255), nullable=False, index=True),
    Column('admin_level', Integer, nullable=False, index=True),
    Column('admin_type', Unicode(64), nullable=False),

    # structure of boundary_parts: "[([way_id], [[way_id]])]"
    Column('boundary_parts', Text),
    GeometryExtensionColumn('boundary', Geometry(dimension=2, srid=900913), nullable=False)
    )

Index('region_boundary_idx', region_table.c.boundary, postgresql_using='gist')


class Region(object):

    __tablename__ = 'region'

    def __init__(self, name, admin_level, admin_type, boundary_parts, boundary):
        self.name = name
        self.admin_level = admin_level
        self.admin_type = admin_type
        self.boundary_parts = boundary_parts
        self.boundary = boundary


region_simplified_table = Table('region_simplified', meta.data,
    Column('id', Integer, primary_key = True),
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
