import urllib
from urlparse import urlparse

from pylons import config, app_globals as g
from pylons import request
from pylons.i18n import _
from paste.deploy.converters import asbool
from adhocracy.model import instance_filter as ifilter
from adhocracy import config as aconfig


CURRENT_INSTANCE = object()


def get_domain_part(domain_with_port):
    return domain_with_port.split(':')[0]


def domain():
    return get_domain_part(config.get('adhocracy.domain'))


def name():
    return config.get('adhocracy.site.name')


def relative_urls(config=config):
    return asbool(config.get('adhocracy.relative_urls', 'false'))


def base_url(path='', instance=CURRENT_INSTANCE, absolute=False,
             append_slash=False, config=config, query_params=None,
             query_string=None, member=None):
    """
    Constructs an URL.

    Path is expected to start with '/'. If not, a relative path to the current
    object will be created.

    If instance isn't defined, the current instance is assumed. Otherwise,
    either an instance, an instance key, or None has to be passed.

    If absolute is True, an absolute URL including the protocol part is
    returned. Otherwise this is avoided, if relative_urls is set to True and
    instance_domains isn't enabled.

    query_params is a dictionary of parameters for the query string of the URL.

    Alternatively to query_params, query_string can be specified which is
    directly used as the query string of the resulting URL.
    """

    if instance == CURRENT_INSTANCE:
        instance = ifilter.get_instance()

    if instance is None:
        instance_key = None
    else:
        if isinstance(instance, (str, unicode)):
            instance_key = instance
        else:
            instance_key = instance.key

    domain = None

    instance_domains = aconfig.get_bool('adhocracy.instance_domains.enabled')

    if instance and instance_domains:
        domain = aconfig.get_json('adhocracy.instance_domains', {})\
            .get(instance_key)

    if domain is not None:
        protocol = config.get('adhocracy.protocol', 'http').strip()
        result = '%s://%s%s' % (protocol, domain, path)

    elif relative_urls(config):

        if instance is None:
            prefix = ''
        else:
            prefix = '/i/' + instance_key

        if absolute or instance_domains:
            protocol = config.get('adhocracy.protocol', 'http').strip()
            domain = config.get('adhocracy.domain').strip()

            result = '%s://%s%s%s' % (protocol, domain, prefix, path)

        else:
            result = '%s%s' % (prefix, path)

    else:

        protocol = config.get('adhocracy.protocol', 'http').strip()
        domain = config.get('adhocracy.domain').strip()

        if instance is None or g.single_instance:
            subdomain = ''
        else:
            subdomain = '%s.' % instance_key

        result = '%s://%s%s%s' % (protocol, subdomain, domain, path)

    if member is not None:
        result += '/' + member

    if result == '':
        result = '/'

    if append_slash and not result.endswith('/'):
        result += '/'

    if query_params:
        result += '&' if '?' in result else '?'
        u = lambda s: unicode(s).encode('utf-8')
        query_params = [(u(k), u(v)) for (k, v) in query_params.iteritems()]
        result += urllib.urlencode(query_params)
    elif query_string:
        result += '&' if '?' in result else '?'
        result += query_string

    return result


def current_url():
    return base_url(request.path)


def shortlink_url(delegateable):
    path = "/d/%s" % delegateable.id
    return base_url(path, None, absolute=True)


def is_local_url(url):
    """check if the url points to this installation of adhocracy to
    avoid fishing attacks and similar.

    see also adhocracy.helpers.is_local_url in adhocracy.js
    """

    if url is None or url == u'':
        return False

    netloc = urlparse(url).netloc
    domain = config.get('adhocracy.domain')

    if netloc == u'' or netloc == domain:
        return True
    elif relative_urls():
        return False
    else:
        # this allows only one subdomain below domain
        return (netloc.endswith(u'.' + domain) and
                (netloc.count(u'.') - domain.count(u'.') == 1))


def velruse_url(path):
    return (aconfig.get('velruse.protocol') + '://' +
            aconfig.get('velruse.domain') + ':' +
            aconfig.get('velruse.port') + '/velruse/' + path.strip('/'))
