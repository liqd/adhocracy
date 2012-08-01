# -*- coding: utf-8 -*-
from sqlalchemy import func
from shapely import wkb
from shapely import wkt
import geojson

from adhocracy.model import meta

import logging
log = logging.getLogger(__name__)

USE_POSTGIS = 'USE_POSTGIS'
USE_SHAPELY = 'USE_SHAPELY'

AVAILABLE_RESOLUTIONS = [
    156543.03390625, 78271.516953125, 39135.7584765625,
    19567.87923828125, 9783.939619140625, 4891.9698095703125,
    2445.9849047851562, 1222.9924523925781, 611.4962261962891,
    305.74811309814453, 152.87405654907226, 76.43702827453613,
    38.218514137268066, 19.109257068634033, 9.554628534317017,
    4.777314267158508, 2.388657133579254, 1.194328566789627,
    0.5971642833948135, 0.29858214169740677, 0.14929107084870338,
    0.07464553542435169]

# FIXME: make configurable - has to be done on client side as well
MIN_ZOOM_LEVEL = 5
MAX_ZOOM_LEVEL = 18

RESOLUTIONS = AVAILABLE_RESOLUTIONS[MIN_ZOOM_LEVEL:MAX_ZOOM_LEVEL + 1]

NUMBER_ZOOM_LEVELS = MAX_ZOOM_LEVEL - MIN_ZOOM_LEVEL + 1

# arbitrary, corresponds to OpenLayers tile sizes
TILE_SIZE_PX = 256

# tolerance resolution in lowest zoom level
MIN_ZOOM_TOLERANCE = 4096.

ZOOM_TOLERANCE = map(lambda e: MIN_ZOOM_TOLERANCE / 2 ** e,
                     range(0, NUMBER_ZOOM_LEVELS))


def format_json_to_geotag(geotag):

    from geoalchemy.utils import to_wkt

    if geotag == '':
        return None

    else:
        return to_wkt(geojson.loads(geotag)['geometry'])


def get_bbox(x, y, zoom):
    tile_size = TILE_SIZE_PX * RESOLUTIONS[zoom]
    bbox = (x * tile_size, y * tile_size,
            (x + 1) * tile_size, (y + 1) * tile_size)
    return func.ST_setsrid(func.box2d('BOX(%f %f, %f %f)' % bbox), 900913)


def get_instance_geo_centre(instance):
    if instance.geo_centre is not None:
        geom = wkb.loads(str(instance.geo_centre.geom_wkb))
    else:
        log.info('setting geo_centre to region centroid for instance %s' %
                 instance.label)
        geom = wkb.loads(str(instance.region.boundary.geom_wkb)).centroid
        instance.geo_centre = wkt.dumps(geom)

    return geom


def add_instance_props(instance, properties):

    def num_pages(instance):
        from adhocracy.model import Page
        pageq = meta.Session.query(Page)
        pageq = pageq.filter(Page.instance == instance)
        return pageq.count()

    properties['num_proposals'] = instance.num_proposals
    properties['num_papers'] = num_pages(instance)
    properties['num_members'] = instance.num_members


