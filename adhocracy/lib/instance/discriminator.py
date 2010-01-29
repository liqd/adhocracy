import logging

import adhocracy.model as model
from pylons import response

log = logging.getLogger(__name__)

class InstanceDiscriminatorMiddleware(object):
    
    TRUNCATE_PREFIX = "www."
    
    def __init__(self, app, domain):
        self.app = app
        self.domain = domain
        log.debug("Host name: %s." % ", ".join(domain))
        
    def __call__(self, environ, start_response):
        host = environ.get('HTTP_HOST', "")
        environ['HTTP_HOST_ORIGINAL'] = host
        port = None
        if ':' in host:
            (host, port) = host.split(':')
        if host.startswith(self.TRUNCATE_PREFIX):
            host = host[len(self.TRUNCATE_PREFIX):]
        
        active_domain = self.domain 
        if host.endswith(self.domain):
            host = host[:len(host)-len(self.domain)]
            if port:
                active_domain = active_domain + ':' + port
        
        environ['adhocracy.domain'] = environ['HTTP_HOST'] = active_domain
        
        instance_key = host.strip('. ').lower()
        if len(instance_key):
            #log.debug("Request instance: %s" % instance_key)
            instance = model.Instance.find(instance_key)
            if not instance:
                log.debug("No such instance: %s, defaulting!" % instance_key)
            else:
                model.filter.setup_thread(instance)
        try:
            return self.app(environ, start_response)
        finally:
            model.filter.setup_thread(None)
             

def setup_discriminator(app, config):
    domains = config.get('adhocracy.domain', config.get('adhocracy.domains', ''))
    domains = [d.strip() for d in domains.split(',')]
    return InstanceDiscriminatorMiddleware(app, domains[0]) 