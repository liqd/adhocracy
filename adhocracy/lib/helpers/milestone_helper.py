import cgi

from pylons.i18n import _

from adhocracy.lib import cache
from adhocracy.lib.helpers import url as _url


@cache.memoize('milestone_link', 3600)
def link(milestone, link=True, **kwargs):
    text = cgi.escape(milestone.title)
    if link and not milestone.is_deleted():
        text = u"<a href='%s'>%s</a>" % (url(milestone, **kwargs),
                                         text)
    return text


@cache.memoize('milestone_url', 3600)
def url(milestone, **kwargs):
    return _url.build(milestone.instance, 'milestone', milestone.id, **kwargs)


@cache.memoize('milestone_bc')
def bc_entity(milestone):
    return _url.BREAD_SEP + _url.link(milestone.title, url(milestone))


def breadcrumbs(milestone):
    bc = _url.root()
    bc += _url.link(_("Milestones"), u'/milestone')
    if milestone is not None:
        bc += bc_entity(milestone)
    return bc
