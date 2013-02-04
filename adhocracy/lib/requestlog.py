import ipaddress

from adhocracy import model

def _anonymize(ipstr):
    ipa = ipaddress.ip_address(ipstr)
    print(dir(ipa))
    raise NotImplementedError()

ANONYMIZATION_FUNCS = {
    'dontlog': lambda ip: None,
    'anonymize': _anonymize,
    'none': lambda ip: ip,
}

class RequestLogger(object):
    def __init__(self, app, config):
        self.app = app
        self.config = config
        afname = self.config.get('adhocracy.requestlog_ipanonymization', 'dontlog')
        self.anonymization_func = ANONYMIZATION_FUNCS[afname]

    def __call__(self, environ, start_response):
        try:
            self.log_request(environ)
        except:
            pass
        return self.app(environ, local_response)

    def log_request(self, environ):
        do_logging = asbool(config.get('adhocracy.enable_request_logging'))
        if do_logging:
            self.log_request(environ)
        
        cookies = environ.get('HTTP_COOKIE')
        user_agent = environ.get('HTTP_USER_AGENT')
        ip_address = self.anonymization_func(adhocracy.lib.util.get_client_ip())

        model.Request.create(ip_adress, environ['PATH_INFO'], cookies, user_agent)
        model.meta.Session.commit()
