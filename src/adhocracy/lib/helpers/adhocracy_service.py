import base64
import json
import magic
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

    #TODO make this a method
    images_get, images_post, images_delete = None, None, None
    """requests prepared requests to call /images"""

    def __init__(self):
        self.staticpages_api_token = config.get(
            'adhocracy_service.staticpages.rest_api_token',
            config.get('adhocracy_service.rest_api_token'))
        self.staticpages_api_address = staticpages_api_address()
        self.staticpages_verify = config.get_bool(
            'adhocracy_service.staticpages.verify_ssl',
            config.get_bool('adhocracy_service.verify_ssl'))
        self.staticpages_headers = {"X-API-Token": self.staticpages_api_token}
        self.api_token = config.get('adhocracy_service.rest_api_token', '')
        self.api_address = config.get('adhocracy_service.rest_api_address', '')
        self.headers = {"X-API-Token": self.api_token}
        self.images_get = requests.Request("GET",
                                           url=self.api_address + "images",
                                           headers=self.headers)
        self.images_post = requests.Request("POST",
                                            url=self.api_address + "images",
                                            headers=self.headers)
        self.images_delete = requests.Request("DELETE",
                                              url=self.api_address + "images",
                                              headers=self.headers)

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

    def add_image(self, filename, binarydata):
        """Post image data to the mediacenter

            returns requests response object
        """
        mimetype = magic.from_buffer(binarydata, mime=True)
        image_encoded = base64.b64encode(binarydata)
        request = self.images_post
        request.data = json.dumps(dict(filename=filename,
                                       data=image_encoded,
                                       mimetype=mimetype,
                                       ))
        return self.session.send(request.prepare())
