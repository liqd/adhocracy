from pylons import config, request, g
from pylons.i18n import _


def name():
    return config.get('adhocracy.site.name', _("Adhocracy"))


def base_url(instance, path=None):
    url = "%s://" % config.get('adhocracy.protocol', 'http').strip()
    if instance is not None and g.single_instance is None:
        url += instance.key + "."
    url += request.environ.get('adhocracy.domain')
    if path is not None:
        url += path
    return url


def shortlink_url(delegateable):
    path = "/d/%s" % delegateable.id
    return base_url(None, path=path)
