from pylons import request

from adhocracy.lib import helpers as h
from adhocracy.lib.base import BaseController
from adhocracy.lib.templating import render_json, render_geojson
from adhocracy.lib.util import get_entity_or_abort
from adhocracy.lib.geo import calculate_tiled_boundaries_json
from adhocracy.lib.geo import calculate_tiled_admin_centres_json
from adhocracy.lib.geo import add_instance_props
from adhocracy.model import meta
from adhocracy.model import Region
from adhocracy.model import Instance
from adhocracy.model import RegionHierarchy

from sqlalchemy import or_

import geojson
from shapely import wkb, wkt

import logging
log = logging.getLogger(__name__)


class GeoController(BaseController):
    
    def get_instances_json(self):
        """
        returns all instances 
        """

        def make_feature(instance):

            if instance.geo_centre is not None:
                geom = wkb.loads(str(instance.geo_centre.geom_wkb))
            else:
                log.info('setting geo_centre to region centroid for instance %s'%instance.name)
                geom = wkb.loads(str(instance.region.boundary.geom_wkb)).centroid
                instance.geo_centre=wkt.dumps(geom)

            return dict(geometry = geom, 
                           properties = {
                               'key': instance.key, 
                               'label': instance.name, 
                               'admin_level': instance.region.admin_level, 
                               'region_id': instance.region.id,
                               })

        instances = meta.Session.query(Instance).filter(Instance.region!=None).all()
        instance_features = map(make_feature, instances)
        return render_geojson(geojson.FeatureCollection([geojson.Feature(**i) for i in instance_features]))


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

        return render_geojson(calculate_tiled_boundaries_json(x, y, zoom, admin_level))


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

        return render_geojson(calculate_tiled_admin_centres_json(x, y, zoom, admin_level))


    @staticmethod
    def get_outer_region(region):
        is_in_q = meta.Session.query(Region).join((RegionHierarchy, Region.id==RegionHierarchy.outer_id))
        is_in_q = is_in_q.filter(RegionHierarchy.inner_id==region.id)
        tl_regions = is_in_q.all() 
        result = filter (lambda r: r.admin_level == region.admin_level-1, tl_regions)
        if (result == []):
            result = filter (lambda r: r.admin_level == region.admin_level-2, tl_regions)
        if (result == []):
            return None
        return result[0]

    def autocomplete_instances_json(self):
        name_contains = request.params.get('name_contains')
        callback = request.params.get('callback')
        q = meta.Session.query(Region).order_by(Region.name)
        q = q.filter(or_(or_(Region.admin_level == 6, Region.admin_level == 7),Region.admin_level == 8))
        q = q.filter(Region.name.ilike('%' + name_contains + '%'))
        regions = q.all()

        def create_entry(region):
            entry = dict()
            entry['name'] = region.name
            outer = self.get_outer_region(region)
            outerNext = outer
            while (outerNext != None):
                outer = outerNext
                outerNext = self.get_outer_region(outer)

            if outer != None: 
                entry['name'] += ', ' + outer.name
            return entry

        response = dict()
        search_result = map(create_entry, regions)

        response['search_result'] = search_result
        return callback + '(' + render_json(response) + ');'

    def find_instances_json(self):
        
        def query_region(item):
            q = meta.Session.query(Region).order_by(Region.name)
            q = q.filter(or_(or_(or_(Region.admin_level == 4,Region.admin_level == 6, Region.admin_level == 7),Region.admin_level == 8)))
#            q = q.filter(Region.name.in_(name_contains))
            q = q.filter(Region.name.ilike('%' + item + '%'))
#            q = q.offset(search_offset).limit(max_rows)
            return q.all()

        def create_entry(region):
            entry = dict()
            if (region != None): 
                instances = getattr(region,"get_instances")
                outer = self.get_outer_region(region)

                entry['name'] = region.name
                entry['region_id'] = region.id
                entry['admin_level'] = region.admin_level
                entry['admin_type'] = region.admin_type
                bbox = wkb.loads(str(region.boundary.geom_wkb)).bounds
                admin_center_props = {
                    'instance_id': "",
                    'admin_level': region.admin_level,
                    'region_id': region.id,
                    'label': region.name,
                    'admin_type': region.admin_type
                }
                entry['bbox'] = '[' + str(bbox[0]) + ',' + str(bbox[1]) + ',' + str(bbox[2]) + ',' + str(bbox[3]) + ']'
                if (outer != None):
                    entry['is_in'] = create_entry(outer)

                if instances != []: 
                    instance = get_entity_or_abort(Instance, instances[0].id)
                    entry['instance_id'] = instance.id
                    entry['url'] = h.entity_url(instances[0])
                    add_instance_props(instance,entry)
                    admin_center_props['instance_id'] = instance.id
                    admin_center_props['url'] = h.entity_url(instances[0])
                    admin_center_props['label'] = instance.label
                    add_instance_props(instance, admin_center_props)
                else: 
                    entry['instance_id'] = ""
                entry['admin_center'] = render_geojson((geojson.Feature(geometry=wkb.loads(str(region.boundary.geom_wkb)).centroid, properties=admin_center_props)))
            return entry
    
        # r1 is_outer region of r2
        def is_outer(name, region):
            outer_region = self.get_outer_region(region)
            if outer_region == None: return False
            elif outer_region.name == name: return True
            else: return is_outer(name,outer_region)

        def merge_lists(a,b):
            a.extend(b)
            return a

#        max_rows = request.params.get('max_rows')
        name_contains = request.params.get('name_contains')
        callback = request.params.get('callback')
#        search_offset = request.params.get('offset')

        search_items = name_contains.split(',')
        for i in range(0,len(search_items)):
            search_items[i] = search_items[i].strip()

        if (len(search_items) == 1 or len(search_items) == 2): 

            search_regions = query_region(search_items[0])
            hit_regions = []
            if (len(search_items) == 2 and len(search_regions) > 1):
                for r in search_regions:
                    if is_outer(search_items[1],r):
                        hit_regions.append(r)
            else:
                hit_regions = search_regions

            response = dict()
#            num_hits = len(regions)

            search_result = map(create_entry, hit_regions)
#            response['count'] = num_hits
            response['search_result'] = search_result
        else:
            resonse['search_result'] = []
        return callback + '(' + render_json(response) + ');'
