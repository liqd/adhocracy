# Copyright 2011 Omniscale (http://omniscale.com)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
log = logging.getLogger(__name__)


from imposm.mapping import (
    Options, FieldType, Polygons, String, Integer, OneOfInt,
    # Points, LineStrings, Bool,
    # set_default_name_type, LocalizedName,
    # WayZOrder, ZOrder, Direction,
    # GeneralizedTable, UnionView,
    # PseudoArea, meter_to_mapunit, sqr_meter_to_mapunit,
    # Options, FieldType,
)

#from imposm.geocoder.mapping import (
    #TrigramString,
    #CityLookupNameGerman,
    #GeometryLineMergeTable, GeometryUnionTable)


# # internal configuration options
# # uncomment to make changes to the default values
# import imposm.config
#
# # import relations with missing rings
# imposm.config.import_partial_relations = False
#
# # select relation builder: union or contains
# imposm.config.relation_builder = 'contains'
#
# # log relation that take longer than x seconds
# imposm.config.imposm_multipolygon_report = 60
#
# # skip relations with more rings (0 skip nothing)
# imposm.config.imposm_multipolygon_max_ring = 0
#
# # split ways that are longer than x nodes (0 to split nothing)
# imposm.config.imposm_linestring_max_length = 50
#
# # cache coords in a compact storage (with delta encoding)
# # use this when memory is limited (default)
# imposm.config.imposm_compact_coords_cache = True

# set_default_name_type(LocalizedName(['name:en', 'int_name', 'name']))

class MultiPolygonString(FieldType):
    """
    A string representing a multipolygon structure. Instead of coordinates, OSM
    ids referencing ways are stored.

    The structure is "[([way_id], [[way_id]])]"

    :PostgreSQL datatype: TEXT
    """
    column_type = "TEXT"

    def value(self, val, osm_elem):
        return str(val)


db_conf = Options(
    db='imposm3',
    host='localhost',
    port=5432,
    user='adhocracy',
    password='adhoc',
    sslmode='allow',
    prefix='osm_',
    proj='epsg:900913',
)


region = Polygons(
    name='region',
    with_type_field=False,
    mapping={
        'boundary': (
            'administrative',
        ),
    },
    fields=(
        ('admin_level', OneOfInt('1 2 3 4 5 6 7 8 9 10 11'.split())),
        #('admin_centre', String()),
        ('de:regionalschluessel', String()),
        ('de:amtlicher_gemeindeschluessel', Integer()),
        ('name:prefix', String()),
        ('postal_code', Integer()),
        ('wikipedia', String()),
        # ('ways', MultiPolygonString()),
    ),
    # admin_center
)

"""
boundary = LineStrings(
    name = 'boundary',
    with_type_field = False,
    mapping = {
        'boundary': (
            'administrative',
        ),
        'admin_level': (),
    },
    fields = (
        ('admin_level', OneOfInt('1 2 3 4 5 6 7 8 9 10 11'.split())),
    ),
)
"""

"""
postal = Polygons(
    name = 'postal',
    with_type_field = True,
    mapping = {
        'boundary': (
            'postal_code',
        ),
        'postal_code': ('__any__',),
        #'openGeoDB:postal_codes': (),
    },
    fields = (
        ('postal_code', String()),
        #('addr:postcode', String()),
        ('postal_code_level', Integer()),
        #('openGeoDB:postal_codes', String()),
    ),
)
"""
