from pylons import tmpl_context as c
from pylons.i18n import _

from sqlalchemy.orm import aliased

from adhocracy import model
from adhocracy.lib import cache
from adhocracy.lib import logo
from adhocracy.lib.helpers import url as _url


def logo_url(category, y, x=None):
    from adhocracy.lib.helpers import base_url
    size = "%s" % y if x is None else "%sx%s" % (x, y)
    filename = u"%s_%s.png" % (category.id, size)
    (path, mtime) = logo.path_and_mtime(category)
    return base_url(u'/category/%s' % filename, query_params={'t': str(mtime)})


def url(category, member=None, **kwargs):
    return _url.build(category.instance, 'category', category.id,
                      member=member, **kwargs)


@cache.memoize('category_bc')
def bc_entity(category):
    return _url.BREAD_SEP + _url.link(category.title, url(category))


def breadcrumbs(category):
    from adhocracy.lib.helpers import base_url
    bc = _url.root()
    bc += _url.link(_("Categories"), base_url(u'/category'))
    if category is not None:
        bc += bc_entity(category)
    return bc


def event_q(category, event_filter=[], count=50):
    """Get events related to this category.

    This is not trivial with our current models. For example this query does
    only include one level of page nesting.
    """
    alias = aliased(model.Delegateable)

    proposal_description_q = model.meta.Session.query(model.Delegateable.id)\
        .join(model.Page._proposal)\
        .join(alias, alias.id == model.Proposal.id)\
        .join(alias.categories)\
        .filter(model.Delegateable.instance == c.instance)\
        .filter(model.CategoryBadge.id == category.id)

    page_child_q = model.meta.Session.query(model.Delegateable.id)\
        .join(alias, model.Delegateable.parents)\
        .join(alias.categories)\
        .filter(model.Delegateable.instance == c.instance)\
        .filter(model.CategoryBadge.id == category.id)

    topic_ids_q = model.meta.Session.query(model.Delegateable.id)\
        .join(model.Delegateable.categories)\
        .filter(model.Delegateable.instance == c.instance)\
        .filter(model.CategoryBadge.id == category.id)\
        .union(proposal_description_q)\
        .union(page_child_q)\
        .distinct()

    events = model.Event.all_q(
        instance=c.instance,
        include_hidden=False,
        event_filter=event_filter)\
        .join(model.Event.topics)\
        .filter(model.Delegateable.id.in_(topic_ids_q))\
        .order_by(model.Event.time.desc())\
        .limit(count)

    return events
