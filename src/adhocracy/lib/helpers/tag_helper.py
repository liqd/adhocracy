import cgi
import math
import urllib

from pylons import tmpl_context as c
from pylons.i18n import _

from adhocracy.lib import cache
from adhocracy.lib.auth import can
from adhocracy.lib.helpers import url as _url
from adhocracy.lib.helpers import url_token
from adhocracy.lib.helpers.site_helper import base_url


def link(tag, count=None, size=None, base_size=12, plain=False, simple=False):
    '''
    Generate a link to a tag. if *simple* is *True* it will create a plain
    <a> link and **ignores all other kwargs!**. If *simple* is *False*,
    it will generate a more fancy link wrapped into a <span>.

    *count* (None or int)
        If an int is given, it will append the count to the link text
    *size* (None or int)
        If given a font-size is set as an inline style.
    *base_size* (int)
        Used to calulate the font size.
    *plain* (boolean)
        Set the 'plain' css class on the wrapper <span>.
    '''
    if simple:
        return u'<a href="%s" rel="tag">%s</a>' % (url(tag),
                                                   cgi.escape(tag.name))

    text = u"<span class='tag_link %s'><a" % ("plain" if plain else "")
    if size is not None:
        size = int(math.sqrt(size) * base_size)
        text += u" style='font-size: %dpx !important;'" % size
    text += u" href='%s' rel='tag'>%s</a>" % (url(tag), cgi.escape(tag.name))
    if count is not None and count > 1:
        text += u"&thinsp;&times;" + str(count)
    text += u"</span>"
    return text


def link_with_untag(tag, delegateable, simple=True):
    tag_link = link(tag, simple=simple)
    if can.instance.edit(c.instance):
        return '%s (%s)' % (
            tag_link,
            '<a href="%s?tag=%d&delegateable=%d&%s">%s</a>' % (
                base_url('/untag_all'),
                tag.id,
                delegateable.id,
                url_token(),
                _('delete')
            )
        )
    else:
        return tag_link


def url(tag, instance=None, **kwargs):
    if instance is None:
        instance = c.instance

    @cache.memoize('tag_url')
    def url_(tag, instance, **kwargs):
        ident = None
        try:
            ident = urllib.quote(tag.name.encode('utf-8'))
        except KeyError:
            ident = tag.id
        return _url.build(instance, u'tag', ident, **kwargs)
    return url_(tag, instance, **kwargs)


def bc_entity(tag):
    return _url.BREAD_SEP + _url.link(tag.name, url(tag))


def breadcrumbs(tag):
    bc = _url.root()
    bc += _url.link(_("Tags"), u'/tag')
    if tag is not None:
        bc += bc_entity(tag)
    return bc
