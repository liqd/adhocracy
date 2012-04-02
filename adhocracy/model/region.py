from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy import Integer, Unicode
from geoalchemy.geometry import MultiPolygon
from geoalchemy import GeometryExtensionColumn, Geometry, GeometryDDL

from adhocracy.model import meta


region_table = Table('region', meta.data,
    Column('id', Integer, primary_key = True),
      # is osm_id
    Column('name', Unicode(255), nullable=False),
    Column('admin_level', Integer, nullable=False),
    Column('admin_type', Unicode(64), nullable=False),
    GeometryExtensionColumn('boundary', Geometry, nullable=False)
    # admin center
    # de:regionalschluessel (12 stellen, numerisch)
    )


class Region(object):

    __tablename__ = 'region'

    def __init__(self, name, admin_level, admin_type, boundary):
        self.name = name
        self.admin_level = admin_level
        self.admin_type = admin_type
        self.boundary = boundary

