from adhocracy.lib import cache
from adhocracy.lib.helpers import url as _url


@cache.memoize('message_url', 3600)
def url(entity, **kwargs):
    return _url.build(entity.instance, 'message', entity.id, **kwargs)
