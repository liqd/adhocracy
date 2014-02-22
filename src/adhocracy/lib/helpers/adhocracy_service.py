import requests

from pylons import config


class RESTAPI(object):
    """Helper to work with the adhocarcy_service rest api
       (adhocracy_kotti.mediacenter, adhocracy_kotti.staticpages, plone).
    """

    session = requests.Session()

    def __init__(self):
        self.api_token = config.get('adhocracy_service.rest_api_token', '')
        self.api_address = config.get('adhocracy_service.rest_api_address', '')
        self.headers = {"X-API-Token": self.api_token}

    def staticpages_get(self, languages):
        request = requests.Request("GET",
                                   url='%s%s' % (
                                       self.api_address,
                                       "staticpages",
                                   ),
                                   params={
                                       'lang': languages,
                                   },
                                   headers=self.headers)

        return self.session.send(request.prepare())

    def staticpage_get(self, path, languages):
        request = requests.Request("GET",
                                   url='%s%s' % (
                                       self.api_address,
                                       'staticpages/single',
                                   ),
                                   params={
                                       'path': path,
                                       'lang': languages,
                                   },
                                   headers=self.headers)

        return self.session.send(request.prepare())
