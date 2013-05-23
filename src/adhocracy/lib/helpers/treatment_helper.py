
from adhocracy.lib import cache
from adhocracy.lib.helpers import url as _url


@cache.memoize('treatment_url', 3600)
def url(entity, **kwargs):
    return _url.build(None, 'admin/treatment', entity.key, **kwargs)
