#!/usr/bin/python
#
# Python REST client library.

__version__ = '0.1'
__description__ = 'The Adhocracy client python package.'
__license__ = 'BSD'

import base64
import json
import logging
import urllib
import urllib2


log = logging.getLogger('adhocracyclient')


class RequestWithMethod(urllib2.Request):

    def __init__(self, method, *args, **kwargs):
        self._method = method
        urllib2.Request.__init__(self, *args, **kwargs)

    def get_method(self):
        return self._method


class AdhocracyClient(object):
    """ Example implementation of a REST client for Adhocracy. """

    base_location = 'http://adhocracy.lan:5000'

    def __init__(self, base_location=None, user=None,
                 password=None, instance=None):
        if base_location is not None:
            self.base_location = base_location
        self.user = user
        self.password = password
        self.instance = None
        if instance:
            self._select(instance)

    def reset(self):
        self.last_status = None
        self.last_body = None
        self.last_headers = None
        self.last_message = None
        self.last_http_error = None
        self.last_url_error = None

    def open_url(self, location, method='GET', data=None, headers={}):
        try:
            if data != None:
                data = urllib.urlencode(data)

            req = RequestWithMethod(method, location, data, headers)

            if self.user is not None and self.password is not None:
                auth = base64.encodestring('%s:%s' % (self.user,
                                                      self.password))
                auth = "Basic %s" % auth
                req.add_header("Authorization", auth)

            self.url_response = urllib2.urlopen(req)
        except urllib2.HTTPError, inst:
            log.debug("adhocracyclient: Received HTTP error code from "
                      "Adhocracy.")
            log.debug("adhocracyclient: location: %s" % location)
            log.debug("adhocracyclient: response code: %s" % inst.fp.code)
            log.debug("adhocracyclient: request headers: %s" % headers)
            log.debug("adhocracyclient: request data: %s" % data)
            self.last_http_error = inst
            self.last_status = inst.code
            self.last_message = inst.read()
        except urllib2.URLError, inst:
            self.last_url_error = inst
            self.last_status, self.last_message = inst.reason
        else:
            log.debug("adhocracyclient: OK opening Adhocracy resource: %s" %
                      location)
            self.last_status = self.url_response.code
            self.last_body = self.url_response.read()
            self.last_headers = self.url_response.headers
            try:
                self.last_message = self.__loadstr(self.last_body)
            except ValueError:
                pass

    def get_location(self, resource_name, entity_id=None,
                     variant=None, member=None, format='json'):
        base = self.base_location
        if self.instance is not None:
            base = self.instance.get('instance_url')
        path = resource_name
        if entity_id is not None:
            path += '/' + str(entity_id)
        if variant is not None:
            path += '/' + variant
        if member is not None:
            path += '/' + member
        url = base + '/' + path
        if format is not None:
            url = url + '.json'
        log.debug("adhocracyclient: request url: %s" % url)
        return url

    def _select(self, key):
        self.instance = self.instance_get(key)

    def instance_index(self):
        self.reset()
        url = self.get_location('instance')
        self.open_url(url)
        return self.last_message

    def instance_get(self, key):
        self.reset()
        url = self.get_location('instance', entity_id=key)
        self.open_url(url)
        return self.last_message

    def proposal_index(self):
        if self.instance is None:
            raise ValueError("No instance is set")
        self.reset()
        url = self.get_location('proposal')
        self.open_url(url)
        return self.last_message

    def proposal_get(self, id):
        if self.instance is None:
            raise ValueError("No instance is set")
        self.reset()
        url = self.get_location('proposal', entity_id=id)
        self.open_url(url)
        return self.last_message

    def proposal_create(self, proposal):
        if self.instance is None:
            raise ValueError("No instance is set")
        self.reset()
        url = self.get_location('proposal', format=None)
        self.open_url(url, method='POST', data=proposal)
        return self.last_message

    def proposal_update(self, proposal):
        if self.instance is None:
            raise ValueError("No instance is set")
        self.reset()
        url = self.get_location('proposal', entity_id=proposal.get('id'),
                                format=None)
        self.open_url(url, method='PUT', data=proposal)
        return self.last_message

    def proposal_delete(self, id):
        if self.instance is None:
            raise ValueError("No instance is set")
        self.reset()
        url = self.get_location('proposal', entity_id=id)
        self.open_url(url, method='DELETE')
        return self.last_message

    def page_index(self):
        if self.instance is None:
            raise ValueError("No instance is set")
        self.reset()
        url = self.get_location('page')
        self.open_url(url)
        return self.last_message

    def page_history(self, id, variant):
        if self.instance is None:
            raise ValueError("No instance is set")
        self.reset()
        url = self.get_location('page', entity_id=id, variant=variant,
                                member='history')
        self.open_url(url)
        return self.last_message

    def page_get(self, id, variant=None):
        if self.instance is None:
            raise ValueError("No instance is set")
        self.reset()
        url = self.get_location('page', entity_id=id, variant=variant,
                                format='json')
        self.open_url(url)
        return self.last_message

    def page_create(self, page):
        if self.instance is None:
            raise ValueError("No instance is set")
        self.reset()
        url = self.get_location('page', format=None)
        self.open_url(url, method='POST', data=page)
        return self.last_message

    def page_update(self, page, variant=None):
        if self.instance is None:
            raise ValueError("No instance is set")
        self.reset()
        url = self.get_location('page', entity_id=page.get('id'),
                                variant=variant, format=None)
        self.open_url(url, method='PUT', data=page)
        return self.last_message

    def page_delete(self, id):
        if self.instance is None:
            raise ValueError("No instance is set")
        self.reset()
        url = self.get_location('page', entity_id=id)
        self.open_url(url, method='DELETE')
        return self.last_message

    #def package_register_get(self):
    #    self.reset()
    #    url = self.get_location('Package Register')
    #    self.open_url(url)
    #    return self.last_message
    #
    #def package_register_post(self, package_dict):
    #    self.reset()
    #    url = self.get_location('Package Register')
    #    data = self.__dumpstr(package_dict)
    #    headers = {'Authorization': self.api_key}
    #    self.open_url(url, data, headers)
    #
    #def package_search(self, q, search_options={}):
    #    self.reset()
    #    url = self.get_location('Package Search')
    #    search_options['q'] = q
    #    data = self.__dumpstr(search_options)
    #    headers = {'Authorization': self.api_key}
    #    self.open_url(url, data, headers)
    #    return self.last_message

    def __dumpstr(self, data):
        return json.dumps(data)

    def __loadstr(self, string):
        return json.loads(string)


#test_prop = {
#    "label": "foo schnasel",
#    "text": "this is an API test foo schnasel",
#    "tags": "tag, tag2, tag3"
#}


#test = AdhocracyClient('http://adhocracy.lan:5000', user='admin',
#                        password='password', instance='schnasel')
