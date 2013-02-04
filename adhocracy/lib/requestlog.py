import ipaddress
import logging

from adhocracy import model

def _anonymize(ipstr):
    ipa = ipaddress.ip_address(unicode(ipstr))
    if ipa.version == 4:
        keep_bits = 24
    elif ipa.version == 6:
        if ipa.ipv4_mapped:
            keep_bits = 120
        else:
            keep_bits = 48
    else:
        raise NotImplementedError()
    mask = ((1 << keep_bits) - 1) << (ipa.max_prefixlen - keep_bits)
    return unicode(type(ipa)(int(ipa) & mask))

ANONYMIZATION_FUNCS = {
    'dontlog': lambda ipstr: None,
    'anonymize': _anonymize,
    'none': lambda ipstr: unicode(ipstr),
}

log = logging.getLogger(__name__)

class RequestLogger(object):
    def __init__(self, app, config):
        self.app = app
        self.config = config
        afname = self.config.get('adhocracy.requestlog_ipanonymization', 'dontlog')
        self.anonymization_func = ANONYMIZATION_FUNCS[afname]

    def __call__(self, environ, start_response):
        try:
            self.log_request(environ)
        except BaseException as e:
            log.error('Error while trying to log request: %r' % e)
        return self.app(environ, local_response)

    def log_request(self, environ):
        do_logging = asbool(config.get('adhocracy.enable_request_logging'))
        if do_logging:
            self.log_request(environ)
        
        cookies = environ.get('HTTP_COOKIE').decode('utf-8', 'replace')
        user_agent = environ.get('HTTP_USER_AGENT').decode('utf-8', 'replace')
        ip_address = self.anonymization_func(adhocracy.lib.util.get_client_ip())

        model.Request.create(ip_adress, environ['PATH_INFO'], cookies, user_agent)
        model.meta.Session.commit()
