import math
import cgi
import urllib

from pylons import tmpl_context as c

from adhocracy.lib import cache

import url as _url

@cache.memoize('tag_link')
def link(tag, count=None, size=None, base_size=12, plain=False):
    text = u"<span class='tag_link %s'><a" % ("plain" if plain else "")
    if size is not None:
        size = int(math.sqrt(size) * base_size)
        text += u" style='font-size: %dpx !important;'" % size
    text += u" href='%s' rel='tag'>%s</a>" % (url(tag), cgi.escape(tag.name))
    if count is not None and count > 1:
        text += u"&thinsp;&times;" + str(count)
    text += u"</span>"
    return text


@cache.memoize('tag_url')
def url(tag, instance=None, **kwargs):
    if instance is None:
        instance = c.instance
    ident = None
    try:
        ident = urllib.quote(tag.name.encode('utf-8'))
    except KeyError:
        ident = tag.id
    return _url.build(instance, u'tag', ident, **kwargs)