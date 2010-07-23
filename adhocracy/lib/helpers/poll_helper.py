
from adhocracy.lib import cache

import url as _url

def url(poll, **kwargs):
    return _url.build(poll.scope.instance, 'poll', poll.id, **kwargs)