from pylons import request

from adhocracy.lib import helpers as h
from adhocracy.lib.base import BaseController
from adhocracy.lib.templating import render_json, render_geojson
from adhocracy.lib.util import get_entity_or_abort
from adhocracy.lib.geo import calculate_tiled_boundaries_json
from adhocracy.lib.geo import calculate_tiled_admin_centres_json
from adhocracy.lib.geo import add_instance_props
from adhocracy.lib.geo import get_instance_geo_centre
from adhocracy.model import meta
from adhocracy.model import Region
from adhocracy.model import Instance
from adhocracy.model import RegionHierarchy

import geojson
from shapely import wkb

import logging
log = logging.getLogger(__name__)


MATCH_WORD_FULL = 'FULL'
MATCH_WORD_START = 'START'
MATCH_WORD_INNER = 'INNER'


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

        return render_geojson(
            calculate_tiled_admin_centres_json(x, y, zoom, admin_level))

    @staticmethod
    def match_substring(column, match_type, query_string):

        match_word_start = match_type in [MATCH_WORD_FULL, MATCH_WORD_START]
        match_word_end = match_type == MATCH_WORD_FULL

        return column.op('~*')(u'.*%s%s%s.*' % (
            '[[:<:]]' if match_word_start else '',
            query_string,
            '[[:>:]]' if match_word_end else ''))

    def get_instance_query(self,
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

    def get_region_query(self,
                         query_entities,
                         match_type,
                         main_query,
                         suffix_query=None):

        # find all (region, instance) tuples, where
        # region matches the given query string
        # and region is inside the returned instance

        query = meta.Session.query(*query_entities)\
            .order_by(Region.name)\
            .filter(self.match_substring(Region.name, match_type, main_query))\
            .join(Region.outer_regions, aliased=True)\
            .filter(Region.id == Instance.region_id)

        if suffix_query:
            query = query\
                .join(Region.outer_regions, aliased=True)\
                .filter(self.match_substring(
                    Region.name, match_type, suffix_query))

        # to include additional information such as the name of the
        # surrounding Landkreis (admin_level=6), a region alias has to
        # be used.
        # from sqlalchemy.orm import aliased
        # region_alias = aliased(Region)
        # meta.Session.query(Instance.id, Region, region_alias.name)
        # [... - as above]
        # .join(Region.outer_regions, aliased=True)\
        # .filter(Region.id == reg.id)\
        # .filter(reg.admin_level==6).all()

        return query

    def get_search_params(self, request):
        query = request.params.get('query')
        query_regions = 'query_regions' in request.params

        search_items = query.split(',', 2)
        main_query = search_items[0].strip()
        if len(search_items) > 1:
            suffix_query = search_items[1].strip()
        else:
            suffix_query = None

        return (main_query, suffix_query)

    def relax_match_type(self, match_type):
        if match_type == MATCH_WORD_FULL:
            return MATCH_WORD_START
        elif match_type == MATCH_WORD_START:
            return MATCH_WORD_INNER
        else:
            return None

    def find_instances_json(self, match_type=MATCH_WORD_FULL):
        """
        returns a dictionary of the following structure

        {
            'instances': [instance_id],
            'regions': [(instance_id, {region_data})]
        }

        the regions list is only returned if the request contains a 'regions'
        parameter.
        """

        (main_query, suffix_query) = self.get_search_params(request)

        instance_query = self.get_instance_query(
            (Instance.id), match_type, main_query, suffix_query)

        instances = [iid for (iid,) in instance_query.all()]

        def create_region_entry(region):

            # FIXME: precalculate bbox and geo_centre for regions
            geom = wkb.loads(str(region.boundary.geom_wkb))

            return {
                'name': region.name,
                'osm_id': region.id,
                'admin_level': region.admin_level,
                'admin_type': region.admin_type,
                'bbox': geom.bounds,
                'geo_centre': geojson.dumps(geom.centroid),
            }

            return entry

        region_query = self.get_region_query(
            (Instance.id, Region), match_type, main_query, suffix_query)

        regions = [(iid, create_region_entry(region))
                   for (iid, region) in region_query.all()]

        if len(instances) == 0 and len(regions) == 0:
            relax_match_type = self.relax_match_type(match_type)
            if relax_match_type is not None:
                return self.autocomplete_instances_json(relax_match_type)

        result = {'instances': instances, 'regions': regions}
        return render_json(result)

    def autocomplete_instances_json(self, match_type=MATCH_WORD_START):
        """
        returns a dictionary of the following structure

        {
            'instances': [instance_id],
            'regions': [(instance_id, {region_data})]
        }

        the regions list is only returned if the request contains a 'regions'
        parameter.
        """

        (main_query, suffix_query) = self.get_search_params(request)

        instance_query = self.get_instance_query(
            (Instance.label), match_type, main_query, suffix_query)

        instances = [label for (label,) in instance_query.all()]

        region_query = self.get_region_query(
            (Instance.label, Region.name),
            match_type,
            main_query,
            suffix_query)

        regions = ['%s, %s' % (region, instance)
                   for (instance, region) in region_query.all()]

        if len(instances) == 0 and len(regions) == 0:
            relax_match_type = self.relax_match_type(match_type)
            if relax_match_type is not None:
                return self.autocomplete_instances_json(relax_match_type)

        result = {'instances': instances, 'regions': regions}
        return render_json(result)
