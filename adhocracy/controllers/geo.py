from adhocracy.lib.base import BaseController

from model.geo import Region

"""
class ApiController(BaseController):

    def regions(self, format='json'):
        callback = self.form_result.get('callback')

        proposals = libsearch.query.run(None, entity_type=model.Proposal)

        if callback:
            d = render_json(proposals)
            response.content_type = 'application/javascript'
            return "%s(%s)" % (callback, d)
        else:
            return render_json(proposals)
"""

from shapely.wkb import loads
import geojson


class ApiController(BaseController):

    def get_features(session, bbox):
        """ bbox format 10 50, 12 60 """

        regions = []

        for region in session.query(Region).filter(Region.geometry.intersects(func.setsrid(func.box2d('BOX(%s)'%bbox),4326))).all():
            regions.append(geojson.Feature(geometry=loads(str(region.geometry.geom_wkb))))

        return geojson.dumps(geojson.FeatureCollection(regions))
