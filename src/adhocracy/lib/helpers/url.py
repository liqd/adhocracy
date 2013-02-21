import cgi
import urllib

from pylons import tmpl_context as c
from webhelpers.text import truncate

from adhocracy.lib.helpers import site_helper as site

BREAD_SEP = " &raquo; "


def append_member_and_format(url, member=None, format=None):
    '''
    Add *member* as the last path segment to the url and
    add the extension .<format> if *format* exists.

    *member*:
        An *unicode* or None
    *format*
        An *unicode* or None

    Returns: An *unicode*
    '''
    if member is not None:
        url += u'/' + member
    if format is not None:
        url += u'.' + format.lower()
    return url


def build(instance, base, id, query=None, anchor=None, member=None,
          format=None, absolute=False):
    '''
    Build an url which will be placed in the subdomain of the
    *instance*'. The url will be composed out of *base* and 'id',
    point to the html id *anchor*.
    '''
    if base:
        base = '/' + base + '/'
    else:
        base = u'/'
    id = id.decode('utf-8') if isinstance(id, str) else unicode(id)
    _path = base + id
    url = site.base_url(_path, instance, absolute=absolute)
    url = append_member_and_format(url, member, format)
    if anchor is not None:
        url += "#" + anchor
    if query is not None:
        for k, v in query.items():
            key = unicode(k).encode('ascii', 'ignore')
            query[key] = unicode(v).encode('utf-8')
        url = url + u'?' + unicode(urllib.urlencode(query))
    return url


def root():
    if c.instance:
        from instance_helper import url
        return link(c.instance.label, url(c.instance)) + BREAD_SEP
    else:
        return link(site.name(), site.base_url(instance=None)) + BREAD_SEP


def link(title, href):
    title = cgi.escape(truncate(title, length=40, whole_word=True))
    return u"<a href='%s'>%s</a>" % (href, title)
