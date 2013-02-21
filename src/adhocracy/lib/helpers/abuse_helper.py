from pylons import tmpl_context as c

from adhocracy.lib.helpers import url as _url


def for_entity(entity):
    from adhocracy.lib.helpers import entity_url
    return for_url(entity_url(entity, absolute=True))


def for_url(url):
    instance = c.instance if c.instance else None
    return _url.build(instance, 'abuse', 'new', query={'url': url})
