from pylons import request

from adhocracy.lib import helpers as h
from adhocracy.lib import cache
from adhocracy.lib.base import BaseController
from adhocracy.lib.templating import render_geojson
from adhocracy.lib.geo import get_instance_geo_centre
from adhocracy.lib.geo import get_bbox
from adhocracy.lib.geo import ZOOM_TOLERANCE
from adhocracy.lib.geo import USE_POSTGIS, USE_SHAPELY
from adhocracy.model import meta
from adhocracy.model import Region
from adhocracy.model import Instance

from sqlalchemy import func
from sqlalchemy import and_
import geojson
from shapely import wkb
from shapely.geometry import box

import logging
log = logging.getLogger(__name__)


MATCH_WORD_FULL = 'FULL'
MATCH_WORD_START = 'START'
MATCH_WORD_INNER = 'INNER'

BBOX_FILTER_TYPE = USE_POSTGIS
SIMPLIFY_TYPE = USE_SHAPELY

class GeoController(BaseController):

    def get_instances_json(self):
        """
        returns all instances
        """

        def make_feature(instance):

            geom = get_instance_geo_centre(instance)

            return dict(geometry=geom,
                        properties={
                            'key': instance.key,
                            'label': instance.name,
                            'admin_level': instance.region.admin_level,
                            'region_id': instance.region.id,
                        })

        instances = meta.Session.query(Instance)\
            .filter(Instance.region != None).all()
        instance_features = map(make_feature, instances)
        return render_geojson(geojson.FeatureCollection(
            [geojson.Feature(**i) for i in instance_features]))

    def get_tiled_boundaries_json(self):
        """
        returns a collection of GeoJSON paths for a given tile, encoded in an
        URL with the following parameters:
         * admin_level
         * x,y - position of the requested tile in the tile grid
         * zoom - zoom level (index in RESOLUTIONS)
        """

        admin_level = int(request.params.get('admin_level'))
        x = int(request.params.get('x'))
        y = int(request.params.get('y'))
        zoom = int(request.params.get('zoom'))

        @cache.memoize('geo_tiled_boundaries')
        def calculate_tiled_boundaries_json(x, y, zoom, admin_level):

            tolerance = ZOOM_TOLERANCE[zoom]
            bbox = get_bbox(x, y, zoom)

            q = meta.Session.query('id', 'name', 'admin_level',
                                   func.ST_AsBinary(func.ST_intersection(
                                       func.st_boundary(Region.boundary.RAW), bbox)))
            q = q.filter(Region.admin_level == admin_level)

            if SIMPLIFY_TYPE == USE_POSTGIS:
                # NYI
                pass

            boundariesRS = q.all()

            def make_feature(region):
                (osm_id, name, admin_level, geom) = region
                return dict(geometry=wkb.loads(str(geom)),
                            properties={'zoom': zoom,
                                        'admin_level': admin_level,
                                        'region_id': osm_id,
                                        'label': name})

            boundaries = map(make_feature, boundariesRS)

            def not_empty(boundary):
                return (boundary['geometry'].geom_type != "GeometryCollection"
                        or not boundary['geometry'].is_empty)
            boundaries = filter(not_empty, boundaries)

            if SIMPLIFY_TYPE == USE_SHAPELY:

                def simplify_region(region):
                    if region['geometry'].is_valid:
                        geom_simple = region['geometry'].simplify(tolerance, True)
                        region['geometry'] = geom_simple
                        if not (geom_simple.is_valid and geom_simple.length > 0):
                            # just send the invalid polygon anyway.
                            log.warn('invalid simplified geometry for %s' %
                                     region['properties']['label'])
                            #import ipdb; ipdb.set_trace()
                    else:
                        log.warn('invalid geometry for %s' %
                                 region['properties']['label'])
                    return region

                boundaries = map(simplify_region, boundaries)

            return geojson.FeatureCollection(
                [geojson.Feature(**r) for r in boundaries])

        return render_geojson(
            calculate_tiled_boundaries_json(x, y, zoom, admin_level))

    def get_admin_centres_json(self):
        """
        returns a collection of GeoJSON points for a given tile, encoded in an
        URL with the following parameters:
         * admin_level
         * x,y - position of the requested tile in the tile grid
         * zoom - zoom level (index in RESOLUTIONS)
        """

        admin_level = request.params.get('admin_level')
        x = int(request.params.get('x'))
        y = int(request.params.get('y'))
        zoom = int(request.params.get('zoom'))

        @cache.memoize('geo_tiled_admin_centres')
        def calculate_tiled_admin_centres_json(x, y, zoom, admin_level):

            bbox = get_bbox(x, y, zoom)

            q = meta.Session.query(Instance)
            q = q.filter(Instance.geo_centre != None)\
                .join(Region).filter(Region.admin_level == admin_level)

            if BBOX_FILTER_TYPE == USE_POSTGIS:
                q = q.filter(func.ST_Contains(bbox,
                             func.ST_setsrid(Instance.geo_centre, 900913)))

            def make_feature(instance):

                return dict(geometry=wkb.loads(str(instance.geo_centre.geom_wkb)),
                            properties={
                                'key': instance.key,
                                'label': instance.label,
                                'admin_level': instance.region.admin_level,
                                'region_id': instance.region.id,
                                'instance_id': instance.id,
                                'num_proposals': instance.num_proposals,
                                'num_members': instance.num_members,
                                'url': h.base_url(instance),
                            })

            instanceResultSet = q.all()

            if BBOX_FILTER_TYPE == USE_SHAPELY:
                sbox = box(*bbox)
                instances = filter(lambda instance: sbox.contains(
                    instance['geo_centre']), map(make_feature, instanceResultSet))

            elif BBOX_FILTER_TYPE == USE_POSTGIS:
                instances = map(make_feature, instanceResultSet)

            return geojson.FeatureCollection([geojson.Feature(**r) for r in instances])

        return render_geojson(
            calculate_tiled_admin_centres_json(x, y, zoom, admin_level))

    @staticmethod
    def match_substring(column, match_type, query_string):

        match_word_start = match_type in [MATCH_WORD_FULL, MATCH_WORD_START]
        match_word_end = match_type == MATCH_WORD_FULL

        return reduce(and_,
                      map(lambda part: column.op('~*')(u'.*%s%s%s.*' % (
                          '[[:<:]]' if match_word_start else '',
                          part,
                          '[[:>:]]' if match_word_end else '')),
                          query_string.split()))

    def query_instances(self,
                        query_entities,
                        match_type,
                        main_query,
                        suffix_query=None):

        query = meta.Session.query(query_entities)\
            .join(Region)\
            .order_by(Region.name)\
            .filter(self.match_substring(Region.name, match_type, main_query))

        if suffix_query is not None and suffix_query != '':
            query = query\
                .join(Region.outer_regions, aliased=True)\
                .filter(self.match_substring(
                    Region.name, match_type, suffix_query))

        return query

    def query_instances_by_region_name(self,
                                       query_entities,
                                       match_type,
                                       main_query,
                                       suffix_query=None):
        """
        Returns a query which returns the columns defined in `query_entities`,
        which are attributes of a region - instance tuple `(r, i)`, which
        fulfills the following criteria:

         - Main_query matches `r.name`.
         - If given, suffix_query matches a region which surrounds `r`.
         - `r == i.region` or `r is surrounded by i.region`.
         - If several regions would result in the same instance, only the one
           with the highest `admin_level` is returned. If there is more such
           hit, any of those but only one is returned.

        To make the query work, `query_entities` must at least include
        `Instance.label`, `Instance.region_id`, `Region.id`, `Region.name` and
        `Region.admin_level`.
        """

        # base_query queries for regions matching the given string and
        # match_type

        base_query = meta.Session.query(*query_entities)\
            .filter(self.match_substring(Region.name, match_type, main_query))

        # if given, suffix_query filters base_query by restricting the hits to
        # those which are surrounded by a region matching suffix_query

        if suffix_query:
            base_query = base_query\
                .join(Region.outer_regions, aliased=True)\
                .filter(self.match_substring(
                    Region.name, match_type, suffix_query))\
                .reset_joinpoint()

        # direct hits filters all regions, which are an instance itself

        direct_hits = base_query\
            .filter(Region.id == Instance.region_id)

        # indirect_hits filters all regions, which are inside an instance

        indirect_hits = base_query\
            .join(Region.outer_regions, aliased=True)\
            .filter(Region.id == Instance.region_id)

        # to return only the region with the highest admin_level, we have to
        # order before applying distinct.

        full_query = direct_hits.union_all(indirect_hits)\
            .order_by(Instance.label, Region.admin_level)\
            .distinct(Instance.label)

        return full_query

        # the ordered_query_stuff below isn't done, because the ORM mapping
        # doesn't seem ot work when using subqueries

        # in order to reorder the query the way we really want we have to wrap
        # the original query in a subquery.

        # ordered_query = meta.Session.query(full_query.subquery())\
        #    .order_by(full_query.c.region_admin_level,
        #              full_query.c.instance_label)

        # return ordered_query

    def get_search_params(self, request):
        query = request.params.get('query')

        search_items = query.split(',', 2)
        main_query = search_items[0].strip()
        if len(search_items) > 1:
            suffix_query = search_items[1].strip()
        else:
            suffix_query = None

        return (query, main_query, suffix_query)

    def relax_match_type(self, match_type):
        if match_type == MATCH_WORD_FULL:
            return MATCH_WORD_START
        elif match_type == MATCH_WORD_START:
            return MATCH_WORD_INNER
        else:
            return None

    def _find_instances(self,
                        make_item_func,
                        query_entities,
                        match_type=MATCH_WORD_START):
        """
        returns a dictionary of the following structure

        {'instances': [instance_dict]}

        the instance_dict structure is defined by the passed `make_item_func`,
        as it is done in `find_instances_json` below.
        """

        (query, main_query, suffix_query) = self.get_search_params(request)

        instances_query = self.query_instances_by_region_name(
            query_entities, match_type, main_query, suffix_query)

        instances = [make_item_func(row) for row in instances_query.all()]

        if len(instances) == 0:
            relax_match_type = self.relax_match_type(match_type)
            if relax_match_type is not None:
                return self._find_instances(
                    make_item_func, query_entities, relax_match_type)

        result = {
            'instances': instances,
            'query_string': query,
        }
        return render_geojson(result)

    def find_instances_json(self):

        def make_item(row):
            (instance, rid, rname, ralevel) = row

            geom = wkb.loads(str(instance.region.boundary.geom_wkb))
            geo_centre = get_instance_geo_centre(instance)

            direct_hit = instance.region_id == rid

            return {
                'id': instance.id,
                'label': instance.label,
                'numProposals': instance.num_proposals,
                'numMembers': instance.num_members,
                'bbox': geom.bounds,
                'geo_centre': geo_centre,
                'url': h.base_url(instance),
                'directHit': direct_hit,
                'regionName': rname,
                'is_authenticated': instance.is_authenticated,
            }

        query_entities = (Instance, Region.id, Region.name, Region.admin_level)

        return self._find_instances(make_item,
                                    query_entities,
                                    MATCH_WORD_FULL)

    def autocomplete_instances_json(self):

        def make_item(row):
            (instance, rid, rname, ralevel) = row

            hit = instance.region_id == rid
            label = rname if hit else '%s, %s' % (rname, instance.label)

            return {
                'id': instance.id,
                'ilabel': instance.label,
                'num_proposals': instance.num_proposals,
                'num_members': instance.num_members,
                'url': h.base_url(instance),
                'region': rname,
                'hit': hit,
                # label is the text which appears in the autocomplete dropdown
                'label': label,
            }

        query_entities = (Instance, Region.id, Region.name, Region.admin_level)

        return self._find_instances(make_item,
                                    query_entities,
                                    MATCH_WORD_START)
