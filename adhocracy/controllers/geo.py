from pylons import request

from adhocracy.lib import helpers as h
from adhocracy.lib.base import BaseController
from adhocracy.lib.templating import render_json, render_geojson
from adhocracy.lib.util import get_entity_or_abort
from adhocracy.lib.geo import USE_POSTGIS 
from adhocracy.lib.geo import USE_SHAPELY
from adhocracy.model import meta
from adhocracy.model import Region
from adhocracy.model import Instance
from adhocracy.model import RegionHierarchy

from sqlalchemy import func
from sqlalchemy import or_

import geojson
from shapely.wkb import loads
from shapely.geometry import Polygon, MultiPolygon, box

import logging
log = logging.getLogger(__name__)

BBOX_FILTER_TYPE = USE_POSTGIS
SIMPLIFY_TYPE = USE_SHAPELY
CENTROID_TYPE = USE_SHAPELY

COMPLEXITY_TOLERANCE = {
    '0': 0.01,
    '1': 0.005,
    '2': 0.001,
    '3': 0.0005,
    '4': 0.0001
    }

class GeoController(BaseController):

    def get_boundaries_json(self):
        admin_level = request.params.get('admin_level')
        
        complexity = request.params.get('complexity')
        tolerance = COMPLEXITY_TOLERANCE[complexity]

        bbox = map(float, request.params.get('bbox').split(','))
        assert(len(bbox)==4)

        q = meta.Session.query(Region)
        q = q.filter(Region.admin_level == admin_level)

        if BBOX_FILTER_TYPE == USE_POSTGIS:
            q = q.filter(Region.boundary.intersects(func.setsrid(func.box2d('BOX(%f %f, %f %f)'%(tuple(bbox))), 4326)))

        if SIMPLIFY_TYPE == USE_POSTGIS:
            # NYI
            pass

        def make_feature(region):
            return dict(geometry = loads(str(region.boundary.geom_wkb)), properties = {'label': region.name, 'admin_level': region.admin_level, 'region_id': region.id})

        def add_admin_center(region):
            regionColumns = filter(lambda r: region['properties']['region_id'] == r.id, regionsResultSet)
            properties = {'admin_level': region['properties']['admin_level'],
                          'label': region['properties']['label'],
                          'region_id': region['properties']['region_id'],
                          'instance_id': ''}
            if regionColumns != []:
                instances = getattr(regionColumns[0],"get_instances")
                if instances != []:
                    properties['url'] = h.base_url(instances[0])
                    properties['label'] = instances[0].label
                    properties['instance_id'] = instances[0].id
            region['properties']['admin_center'] = geojson.Feature(geometry=region['geometry'].centroid, properties=properties)
            return region

        regionsResultSet = q.all()

        if BBOX_FILTER_TYPE == USE_SHAPELY:
            sbox = box(*bbox)
            regions = filter(lambda region: sbox.intersection(region['geometry']), map(make_feature, regionsResultSet))

        elif BBOX_FILTER_TYPE == USE_POSTGIS:

            regions = map(make_feature, regionsResultSet)

        if SIMPLIFY_TYPE == USE_SHAPELY:

            def simplify_region(region):
                if region['geometry'].is_valid:
                    geom_simple = region['geometry'].simplify(tolerance, True)
                    if geom_simple.is_valid and geom_simple.area != 0:
                        region['geometry'] = geom_simple
                    else:
                        log.warn('invalid simplified geometry for %s'%region['properties']['label'])
                else:
                    log.warn('invalid geometry for %s'%region['properties']['label'])
                return region

            regions = map(simplify_region, regions)

        if CENTROID_TYPE == USE_POSTGIS:
            #NYI
            pass

        if CENTROID_TYPE == USE_SHAPELY:
            regions = map(add_admin_center, regions)

        return render_geojson(geojson.FeatureCollection([geojson.Feature(**r) for r in regions]))

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
                bbox = loads(str(region.boundary.geom_wkb)).bounds
                admin_center_props = {
                    'instance_id': "",
                    'admin_level': region.admin_level,
                    'region_id': region.id,
                    'label': region.name
                }
                entry['bbox'] = '[' + str(bbox[0]) + ',' + str(bbox[1]) + ',' + str(bbox[2]) + ',' + str(bbox[3]) + ']'
                if (outer != None):
                    entry['is_in'] = create_entry(outer)

                if instances != []: 
                    instance = get_entity_or_abort(Instance, instances[0].id)
                    entry['instance_id'] = instance.id
                    entry['url'] = h.entity_url(instances[0])
                    entry['num_proposals'] = instance.num_proposals
                    entry['num_papers'] = num_pages(instance)
                    entry['num_members'] = instance.num_members
                    entry['create_date'] = str(instance.create_time.date())
                    admin_center_props['instance_id'] = instance.id
                    admin_center_props['url'] = h.entity_url(instances[0])
                    admin_center_props['label'] = instance.label
                else: 
                    entry['instance_id'] = ""
                entry['admin_center'] = render_geojson((geojson.Feature(geometry=loads(str(region.boundary.geom_wkb)).centroid, properties=admin_center_props)))
            return entry
    
        def num_pages(instance):
            from adhocracy.model import Page
            pageq = meta.Session.query(Page)
            pageq = pageq.filter(Page.instance == instance)
            return pageq.count()

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
