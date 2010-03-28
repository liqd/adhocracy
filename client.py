__version__ = '0.1'
__description__ = 'The Adhocracy client Python package.'
__license__ = 'BSD'

import os, urllib, urllib2, base64
import logging
logger = logging.getLogger('adhocracyclient')

class RequestWithMethod(urllib2.Request):

    def __init__(self, method, *args, **kwargs):
        self._method = method
        urllib2.Request.__init__(self, *args, **kwargs)

    def get_method(self):
        return self._method


class AdhocracyClient(object):
    
    base_location = 'http://liqd.net'

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
            if self.user is not None and self.password is not None:
                passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
                passman.add_password(None, location, self.user, self.password)
                authhandler = urllib2.HTTPBasicAuthHandler(passman)
                opener = urllib2.build_opener(authhandler)
                urllib2.install_opener(opener)
            
            if data != None:
                data = urllib.urlencode({data: 1}) 
            req = RequestWithMethod(method, location, data, headers)
            self.url_response = urllib2.urlopen(req)
        except urllib2.HTTPError, inst:
            print "adhocracyclient: Received HTTP error code from Adhocracy."
            print "adhocracyclient: location: %s" % location
            print "adhocracyclient: response code: %s" % inst.fp.code
            print "adhocracyclient: request headers: %s" % headers
            print "adhocracyclient: request data: %s" % data
            self.last_http_error = inst
            self.last_status = inst.code
            self.last_message = inst.read()
        except urllib2.URLError, inst:
            self.last_url_error = inst
            self.last_status,self.last_message = inst.reason
        else:
            print "adhocracyclient: OK opening Adhocracy resource: %s" % location
            self.last_status = self.url_response.code
            self.last_body = self.url_response.read()
            self.last_headers = self.url_response.headers
            try:
                self.last_message = self.__loadstr(self.last_body)
            except ValueError:
                pass
    
    
    def get_location(self, resource_name, entity_id=None, member=None):
        base = self.base_location
        if self.instance is not None:
            base = self.instance.get('instance_url')
        path = resource_name
        if entity_id is not None:
            path += '/' + entity_id
        if member is not None:
            path += '/' + member
        url = base + '/' + path + '.json'
        print "adhocracyclient: request url: %s" % url
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
        try: # since python 2.6
            import json
        except ImportError: 
            import simplejson as json
        return json.dumps(data)
    
    def __loadstr(self, string):
        try: # since python 2.6
            import json
        except ImportError: 
            import simplejson as json
        return json.loads(string)


test = AdhocracyClient('http://adhocracy.lan:5000', user='admin', 
                        password='password', instance='schnasel')