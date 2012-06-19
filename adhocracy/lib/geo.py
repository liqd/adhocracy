from sqlalchemy import func
from geoalchemy import functions
import geojson
from shapely import wkb
from shapely.geometry import box

from adhocracy.lib import cache
from adhocracy.lib import helpers as h
from adhocracy.model import meta
from adhocracy.model import Instance
from adhocracy.model import Region

import logging
log = logging.getLogger(__name__)

USE_POSTGIS = 'USE_POSTGIS'
USE_SHAPELY = 'USE_SHAPELY'

BBOX_FILTER_TYPE = USE_POSTGIS
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
MIN_ZOOM_TOLERANCE = 1000.

ZOOM_TOLERANCE = map(lambda e:MIN_ZOOM_TOLERANCE/2**e, range(0,NUMBER_ZOOM_LEVELS))


def format_json_to_geotag(geotag):

    import geojson
    from geoalchemy.utils import to_wkt

    if geotag == '':
        return None

    else:
        return to_wkt(geojson.loads(geotag)['geometry'])


def get_bbox(x, y, zoom):
    tile_size = TILE_SIZE_PX * RESOLUTIONS[zoom]
    bbox = (x * tile_size, y * tile_size,
            (x+1) * tile_size, (y+1) * tile_size)
    return func.ST_setsrid(func.box2d('BOX(%f %f, %f %f)'%bbox), 900913)


@cache.memoize('geo_tiled_boundaries')
def calculate_tiled_boundaries_json(x, y, zoom, admin_level):

    tolerance = ZOOM_TOLERANCE[zoom]
    bbox = get_bbox(x, y, zoom)

    q = meta.Session.query('id', 'name', 'admin_level',
            func.ST_AsBinary(func.ST_intersection(func.st_boundary(Region.boundary.RAW), bbox)))
    q = q.filter(Region.admin_level == admin_level)

    if SIMPLIFY_TYPE == USE_POSTGIS:
        # NYI
        pass

    boundariesRS = q.all()

    def make_feature(region):
        (osm_id, name, admin_level, geom) = region
        return dict(geometry = wkb.loads(str(geom)), 
                    properties = {'zoom': zoom, 
                                  'admin_level': admin_level,
                                  'region_id': osm_id,
                                  'label': name})

    boundaries = map(make_feature, boundariesRS)
    def not_empty(boundary):
        return (boundary['geometry'].geom_type != "GeometryCollection"
                or not boundary['geometry'].is_empty)
    boundaries = filter (not_empty, boundaries)

    if SIMPLIFY_TYPE == USE_SHAPELY:

        def simplify_region(region):
            if region['geometry'].is_valid:
                geom_simple = region['geometry'].simplify(tolerance, True)
                region['geometry'] = geom_simple
                if not (geom_simple.is_valid and geom_simple.length > 0):
                    # just send the invalid polygon anyway.
                    log.warn('invalid simplified geometry for %s'%region['properties']['label'])
                    #import ipdb; ipdb.set_trace()
            else:
                log.warn('invalid geometry for %s'%region['properties']['label'])
            return region

        boundaries = map(simplify_region, boundaries)

    return geojson.FeatureCollection([geojson.Feature(**r) for r in boundaries])


@cache.memoize('geo_tiled_admin_centres')
def calculate_tiled_admin_centres_json(x, y, zoom, admin_level):

    bbox = get_bbox(x, y, zoom)

    q = meta.Session.query(Instance)
    q = q.filter(Instance.geo_centre != None).join(Region).filter(Region.admin_level == admin_level)

    if BBOX_FILTER_TYPE == USE_POSTGIS:
        q = q.filter(func.ST_Contains(bbox, func.ST_setsrid(Instance.geo_centre, 900913)))

    def make_feature(instance):

        return dict(geometry = wkb.loads(str(instance.geo_centre.geom_wkb)),
                       properties = {
                           'key': instance.key,
                           'label': instance.label,
                           'admin_level': instance.region.admin_level, 
                           'region_id': instance.region.id,
                           'instance_id': instance.id,
                           'num_proposals': instance.num_proposals,
                           'num_members': instance.num_members,
                           'url': h.base_url(instance),
                           })
    """ 
    instance_id: item.instance_id,
    region_id: item.region_id,
    label: item.name,
    url: item.url,
    value: item.name,
    num_proposals: item.num_proposals,
    num_papers: item.num_papers,
    num_members: item.num_members,
    create_date: item.create_date,
    bbox: item.bbox,
    admin_center: feature,
    admin_type: item.admin_type,
    is_in: item.is_in
    """

    instanceResultSet = q.all()

    if BBOX_FILTER_TYPE == USE_SHAPELY:
        sbox = box(*bbox)
        instances = filter(lambda instance: sbox.contains(instance['geo_centre']), map(make_feature, instanceResultSet))

    elif BBOX_FILTER_TYPE == USE_POSTGIS:
        instances = map(make_feature, instanceResultSet)

    return geojson.FeatureCollection([geojson.Feature(**r) for r in instances])


def add_instance_props(instance, properties):

    def num_pages(instance):
        from adhocracy.model import Page
        pageq = meta.Session.query(Page)
        pageq = pageq.filter(Page.instance == instance)
        return pageq.count()

    properties['num_proposals'] = instance.num_proposals
    properties['num_papers'] = num_pages(instance)
    properties['num_members'] = instance.num_members
    properties['create_date'] = str(instance.create_time.date())
        
