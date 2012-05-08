import logging

from adhocracy import model
from pylons import config

log = logging.getLogger(__name__)


class InstanceDiscriminatorMiddleware(object):

    def __init__(self, app, domain):
        self.app = app
        self.domain = domain
        log.debug("Host name: %s." % domain)

    def __call__(self, environ, start_response):
        host = environ.get('HTTP_HOST', "")
        environ['adhocracy.domain'] = self.domain
        instance_key = config.get('adhocracy.instance')
        if instance_key is None:
            host = host.replace(self.domain, "")
            host = host.split(':', 1)[0]
            host = host.strip('.').strip()
            instance_key = host

        if len(instance_key):
            instance = model.Instance.find(instance_key)
            if instance is None:
                log.debug("No such instance: %s, defaulting!" % instance_key)
            else:
                model.instance_filter.setup_thread(instance)
        try:
            return self.app(environ, start_response)
        finally:
            model.instance_filter.setup_thread(None)


def setup_discriminator(app, config):
    # warn if abdoned adhocracy.domains is used
    if config.get('adhocracy.domains') is not None:
        raise AssertionError('adhocracy.domains is not supported anymore. '
                             'use adhocracy.domain (without the s) with only '
                             'one domain')
    domain = config.get('adhocracy.domain').strip()
    return InstanceDiscriminatorMiddleware(app, domain)
