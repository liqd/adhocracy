import urllib
import adhocracy.model as model
from adhocracy.lib import text
from pylons import tmpl_context as c, request


def instance_url(instance, path=None):
    url = "http://"
    if instance is not None:
        url += instance.key + u"."
    url += request.environ.get('adhocracy.domain')
    port = int(request.environ.get('SERVER_PORT'))
    if port != 80:
        url += ':' + str(port)
    if path is not None:
        url += path
    return url

    
def append_member_and_format(url, member=None, format=None):
    if member is not None:
        url += u'/' + member
    if format is not None:
        url += u'.' + format.lower()
    return url


def build(instance, base, id, query=None, **kwargs):
    url = instance_url(instance, path=u'/' + base + u'/' + unicode(id))
    url = append_member_and_format(url, **kwargs)
    if query is not None:
        for k, v in query.items():
            query[unicode(k).encode('ascii', 'ignore')] = unicode(v).encode('utf-8')
        url = url + u'?' + unicode(urllib.urlencode(query))
    return url #.encode('utf-8')
