from pylons import config, app_globals as g
from pylons.i18n import _
from paste.deploy.converters import asbool
from adhocracy.model import instance_filter as ifilter


CURRENT_INSTANCE = object()


def domain():
    return config.get('adhocracy.domain').split(':')[0]


def name():
    return config.get('adhocracy.site.name', _("Adhocracy"))


def base_url(path='', instance=CURRENT_INSTANCE, absolute=False,
             append_slash=False, config=config):
    """
    Constructs an URL.

    Path is expected to start with '/'. If not, a relative path to the current
    object will be created.

    If instance isn't defined, the current instance is assumed. Otherwise,
    either an instance instance or None has to be passed.

    If absolute is True, an absolute URL including the protocol part is
    returned. Otherwise this is avoided, if relative_urls is set to True.
    """

    if instance == CURRENT_INSTANCE:
        instance = ifilter.get_instance()

    if asbool(config.get('adhocracy.relative_urls', 'false')):

        if instance is None:
            prefix = ''
        else:
            prefix = '/i/' + instance.key

        if absolute:
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
            subdomain = '%s.' % instance.key

        result = '%s://%s%s%s' % (protocol, subdomain, domain, path)

    if result == '':
        result = '/'

    if append_slash and not result.endswith('/'):
        result += '/'

    return result


def shortlink_url(delegateable):
    path = "/d/%s" % delegateable.id
    return base_url(path, None, absolute=True)
