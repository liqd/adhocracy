from pylons import config, g
from pylons.i18n import _
from paste.deploy.converters import asbool
from adhocracy.model import meta, instance_filter as ifilter


CURRENT_INSTANCE = object()


def domain():
    return config.get('adhocracy.domain').split(':')[0]


def name():
    return config.get('adhocracy.site.name', _("Adhocracy"))

def base_url(path='', instance=CURRENT_INSTANCE, absolute=False):
    """
    Constructs an URL.

    Path is expected to start with '/'. If not, a relative path to the current
    object will be created. 

    If instance isn't defined, the current instance is assumed. Otherwise,
    either an instance instance or None has to be passed.

    If absolute is True, an absolute URL including the protocol part is
    returned. Otherwise this is avoided if the resulting URL has the same
    domain part as the current URL.
    """

    if asbool(config.get('adhocracy.relative_urls', 'false')):
        if instance == CURRENT_INSTANCE:
            instance = ifilter.get_instance()

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
        current_instance = ifilter.get_instance()

        if instance == CURRENT_INSTANCE:
            instance = current_instance
        elif instance != current_instance:
            absolute = True

        if absolute:

            protocol = config.get('adhocracy.protocol', 'http').strip()
            domain = config.get('adhocracy.domain').strip()

            if instance is None or g.single_instance:
                subdomain = ''
            else:
                subdomain = '%s.' % instance.key

            result = '%s://%s%s%s' % (protocol, subdomain, domain, path)

        else:
            result = path

    if result == '':
        result = '/'

    return result


def shortlink_url(delegateable):
    path = "/d/%s" % delegateable.id
    return base_url(path, None, absolute=True)
