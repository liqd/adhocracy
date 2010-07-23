
from adhocracy.lib import cache

import url as _url

@cache.memoize('delegation_url')
def url(delegation, **kwargs):
    return _url.build(delegation.scope.instance, 'delegation', delegation.id, **kwargs)