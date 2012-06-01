from pylons import config, g
from pylons.i18n import _
from paste.deploy.converters import asbool

def domain():
    return config.get('adhocracy.domain').split(':')[0]


def name():
    return config.get('adhocracy.site.name', _("Adhocracy"))


def base_url(instance, path=None):
    if asbool(config.get('adhocracy.urls_without_hostname', 'false')):
        url = ''
        if instance is not None:
            url = '/i/' + instance.key
    else:
        url = "%s://" % config.get('adhocracy.protocol', 'http').strip()
        if instance is not None and g.single_instance is None:
            url += instance.key + "."
        url += config.get('adhocracy.domain').strip()
    if path is None:
        url += '/'
    else:
        url += path
    return url


def shortlink_url(delegateable):
    path = "/d/%s" % delegateable.id
    return base_url(None, path=path)
