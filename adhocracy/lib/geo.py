from sqlalchemy import func

import geojson
from shapely.wkb import loads

from adhocracy.lib import cache
from adhocracy.model import meta
from adhocracy.model import Region

import logging
log = logging.getLogger(__name__)

USE_POSTGIS = 'USE_POSTGIS'
USE_SHAPELY = 'USE_SHAPELY'

SIMPLIFY_TYPE = USE_SHAPELY

AVAILABLE_RESOLUTIONS = [156543.03390625, 78271.516953125, 39135.7584765625, 19567.87923828125, 9783.939619140625, 4891.9698095703125, 2445.9849047851562, 1222.9924523925781, 611.4962261962891, 305.74811309814453, 152.87405654907226, 76.43702827453613, 38.218514137268066, 19.109257068634033, 9.554628534317017, 4.777314267158508, 2.388657133579254, 1.194328566789627, 0.5971642833948135, 0.29858214169740677, 0.14929107084870338, 0.07464553542435169]

# FIXME: make configurable - has to be done on client side as well
MIN_ZOOM_LEVEL = 5
MAX_ZOOM_LEVEL = 18

RESOLUTIONS = AVAILABLE_RESOLUTIONS[MIN_ZOOM_LEVEL:MAX_ZOOM_LEVEL+1]

NUMBER_ZOOM_LEVELS = MAX_ZOOM_LEVEL - MIN_ZOOM_LEVEL + 1

# arbitrary, corresponds to OpenLayers tile sizes
TILE_SIZE_PX = 256

# tolerance resolution in lowest zoom level
MIN_ZOOM_TOLERANCE = 4096.

ZOOM_TOLERANCE = map(lambda e:MIN_ZOOM_TOLERANCE/2**e, range(0,NUMBER_ZOOM_LEVELS))


def format_json_to_geotag(geotag):

    import geojson
    from geoalchemy.utils import to_wkt

    if geotag == '':
        return None

    else:
        return to_wkt(geojson.loads(geotag)['geometry'])


@cache.memoize('geo_tiled_boundaries')
def calculate_tiled_boundaries_json(x, y, zoom, admin_level):

    tolerance = ZOOM_TOLERANCE[zoom]
    tile_size = TILE_SIZE_PX * RESOLUTIONS[zoom]
    bbox = [ x * tile_size, y * tile_size, 
            (x+1) * tile_size, (y+1) * tile_size]

    q = meta.Session.query(func.ST_AsBinary(func.ST_intersection(func.st_boundary(Region.boundary.RAW),
                                            func.ST_setsrid(func.box2d('BOX(%f %f, %f %f)'%(tuple(bbox))),900913))))
    q = q.filter(Region.admin_level == admin_level)

    if SIMPLIFY_TYPE == USE_POSTGIS:
        # NYI
        pass

    boundariesRS = q.all()

    def make_feature(boundary):
        geom = loads(str(boundary[0]))
        return dict(geometry = geom, properties = {'zoom': zoom, 
                                                   'admin_level': admin_level,
                                                   'label': ''})

    boundaries = map(make_feature, boundariesRS)
    def not_empty(boundary):
        return (boundary['geometry'].geom_type != "GeometryCollection"
                or not boundary['geometry'].is_empty)
    boundaries = filter (not_empty, boundaries)

    if SIMPLIFY_TYPE == USE_SHAPELY:

        def simplify_region(region):
            if region['geometry'].is_valid:
                geom_simple = region['geometry'].simplify(tolerance, True)
                # import ipdb; ipdb.set_trace()
                if geom_simple.is_valid and geom_simple.length > 0:
                    region['geometry'] = geom_simple
                else:
                    log.warn('invalid simplified geometry for %s'%region['properties']['label'])
            else:
                log.warn('invalid geometry for %s'%region['properties']['label'])
            return region

        boundaries = map(simplify_region, boundaries)

    return geojson.FeatureCollection([geojson.Feature(**r) for r in boundaries])
