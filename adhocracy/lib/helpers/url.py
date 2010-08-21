import urllib
import cgi

from pylons import tmpl_context as c
from webhelpers.text import truncate

BREAD_SEP = " &raquo; "

import site_helper as site


def append_member_and_format(url, member=None, format=None):
    if member is not None:
        url += u'/' + member
    if format is not None:
        url += u'.' + format.lower()
    return url


def build(instance, base, id, query=None, anchor=None, **kwargs):
    url = site.base_url(instance, path=u'/' + base + u'/' + unicode(id))
    url = append_member_and_format(url, **kwargs)
    if anchor is not None:
        url += "#" + anchor
    if query is not None:
        for k, v in query.items():
            query[unicode(k).encode('ascii', 'ignore')] = unicode(v).encode('utf-8')
        url = url + u'?' + unicode(urllib.urlencode(query))
    return url #.encode('utf-8')


def root():
    if c.instance:
        from instance_helper import url
        return link(c.instance.label, url(c.instance)) + BREAD_SEP
    else:
        return link(site.name(), site.base_url(None)) + BREAD_SEP


def link(title, href):
    title = cgi.escape(truncate(title, length=40, whole_word=True))
    return u"<a href='%s'>%s</a>" % (href, title)