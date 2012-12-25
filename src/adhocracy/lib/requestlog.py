import ipaddress
import logging

import adhocracy.lib.util
import adhocracy.model


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
    intf = ipaddress.ip_interface(u'%s/%s' % (ipa, keep_bits))
    return unicode(intf.network.network_address)

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
        afname = self.config.get('adhocracy.requestlog_ipanonymization',
                                 'dontlog')
        self.anonymization_func = ANONYMIZATION_FUNCS[afname]

    def __call__(self, environ, start_response):
        try:
            self.log_request(environ)
        except BaseException as e:
            log.error('Error while trying to log request: %r' % e)
        return self.app(environ, start_response)

    def log_request(self, environ):
        def _get_field(name):
            res_bytes = environ.get(name)
            if res_bytes is None:
                return None
            return res_bytes.decode('utf-8', 'replace')

        full_ip = adhocracy.lib.util.get_client_ip(environ)
        ip = self.anonymization_func(full_ip)
        url = (environ['PATH_INFO'].decode('utf-8', 'replace')
               + '?' + environ['QUERY_STRING'].decode('utf-8', 'replace'))

        adhocracy.model.RequestLog.create(ip, url,
                                    cookies=_get_field('HTTP_COOKIE'),
                                    user_agent=_get_field('HTTP_USER_AGENT'),
                                    referer=_get_field('HTTP_REFERER')
        )
        adhocracy.model.meta.Session.commit()
