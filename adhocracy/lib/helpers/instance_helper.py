
from adhocracy.lib import url as _url
from adhocracy.lib import cache

def url(instance, member=None, format=None, **kwargs):
    return _url.build(instance, 'instance', instance.key, member=member, format=format, **kwargs)