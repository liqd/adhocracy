from adhocracy.lib import url as _url
from adhocracy.lib import cache

def url(poll, **kwargs):
    return _url.build(poll.scope.instance, 'poll', poll.id, **kwargs)