import requests
from collections import OrderedDict

from pylons import tmpl_context as c

from adhocracy import config
from adhocracy import i18n


def instance_staticpages_api_address():
    if c.instance:
        key = 'adhocracy.instance-%s.staticpages.rest_api_address'
        return config.get(key % c.instance.key, '')
    else:
        return ''


def staticpages_api_address():
    ret = instance_staticpages_api_address()
    if ret == '':
        ret = config.get('adhocracy_service.staticpages.rest_api_address')
    if ret == '':
        ret = config.get('adhocracy_service.rest_api_address')
    return ret


class RESTAPI(object):
    """Helper to work with the adhocarcy_service rest api
       (adhocracy_kotti.mediacenter, adhocracy_kotti.staticpages, plone).
    """

    session = requests.Session()

    def __init__(self):
        self.staticpages_api_token = config.get(
            'adhocracy_service.staticpages.rest_api_token',
            config.get('adhocracy_service.rest_api_token'))
        self.staticpages_api_address = staticpages_api_address()
        self.staticpages_verify = config.get_bool(
            'adhocracy_service.staticpages.verify_ssl',
            config.get_bool('adhocracy_service.verify_ssl'))
        self.staticpages_headers = {"X-API-Token": self.staticpages_api_token}

    def staticpages_get(self, base=None, languages=None):
        if languages is None:
            languages = i18n.all_languages(include_preferences=True)
        params = OrderedDict({
            'lang': languages
        })
        if base is not None:
            params['base'] = base
        request = requests.Request("GET",
                                   url='%s%s' % (
                                       self.staticpages_api_address,
                                       "staticpages",
                                   ),
                                   params=params,
                                   headers=self.staticpages_headers)
        return self.session.send(request.prepare(),
                                 verify=self.staticpages_verify)

    def staticpage_get(self, path, languages=None):
        if languages is None:
            languages = i18n.all_languages(include_preferences=True)
        request = requests.Request("GET",
                                   url='%s%s' % (
                                       self.staticpages_api_address,
                                       'staticpages/single',
                                   ),
                                   params=OrderedDict({
                                       'path': path,
                                       'lang': languages,
                                   }),
                                   headers=self.staticpages_headers)

        return self.session.send(request.prepare(),
                                 verify=self.staticpages_verify)
