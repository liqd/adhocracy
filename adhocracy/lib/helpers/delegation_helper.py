from adhocracy.lib import url as _url
from adhocracy.lib import cache


@cache.memoize('delegation_url')
def url(delegation, **kwargs):
    return _url.build(delegation.scope.instance, 'delegation', delegation.id, **kwargs)