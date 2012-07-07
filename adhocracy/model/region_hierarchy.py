from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy import Integer

from adhocracy.model import meta


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
