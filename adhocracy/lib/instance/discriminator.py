import logging

import adhocracy.model as model
from pylons import response

log = logging.getLogger(__name__)

class InstanceDiscriminatorMiddleware(object):
    
    TRUNCATE_PREFIX = "www."
    
    def __init__(self, app, domains):
        self.app = app
        self.domains = domains
        log.debug("VHosts: %s." % ", ".join(domains))
        
    def __call__(self, environ, start_response):
        host = environ.get('HTTP_HOST', "")
        environ['HTTP_HOST_ORIGINAL'] = host
        port = None
        if ':' in host:
            (host, port) = host.split(':')
        if host.startswith(self.TRUNCATE_PREFIX):
            host = host[len(self.TRUNCATE_PREFIX):]
        
        environ['adhocracy.active.domain'] = self.domains[0]
        for domain in self.domains:
            if host.endswith(domain):
                host = host[:len(host)-len(domain)]
                if port:
                    environ['adhocracy.active.domain'] = environ['HTTP_HOST'] = domain + ':' + port
                else:
                    environ['adhocracy.active.domain'] = environ['HTTP_HOST'] = domain
                #environ['HTTP_HOST'] = '.' + domain repoze auth tkt cookie hack 
                break
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
    domains = config.get('adhocracy.domains', '')
    domains = [d.strip() for d in domains.split(',')]
    return InstanceDiscriminatorMiddleware(app, domains) 