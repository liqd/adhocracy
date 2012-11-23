from pylons import config, g
from pylons.i18n import _
from paste.deploy.converters import asbool

def domain():
    return config.get('adhocracy.domain').split(':')[0]


def name():
    return config.get('adhocracy.site.name', _("Adhocracy"))

def absolute_url(instance, path=None):
    """
    Get the base URL for an instance (optionally extended by path).
    This will always be an absolute/full URL (starting with https:// )
    """
    url = "%s://" % config.get('adhocracy.protocol', 'http').strip()
    if instance is not None and g.single_instance is None:
        url += instance.key + "."
    url += config.get('adhocracy.domain').strip()
    url += '/' if path is None else path
    return url

def base_url(instance, path=None):
    """
    Get the base URL for an instance (optionally extended by path).
    Can be relative ( like /instance/foo ), so use absolute_url
    instead if you want a full URL starting with https:// .
    """
    if asbool(config.get('adhocracy.relative_urls', 'false')):
        url = ''
        if instance is not None:
            url = '/i/' + instance.key
        url += '/' if path is None else path
        return url
    else:
        return absolute_url(instance, path)

def shortlink_url(delegateable):
    path = "/d/%s" % delegateable.id
    return base_url(None, path=path)
