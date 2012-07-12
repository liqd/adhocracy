from adhocracy.lib.helpers.site_helper import base_url

def openlayers_url():
#    return "http://openlayers.org/api/2.12/OpenLayers.js"
    return base_url(None, path="/fanstatic/openlayers/:version:2.12.0/openlayers.min.js")

