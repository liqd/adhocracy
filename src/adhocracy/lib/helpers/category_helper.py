from pylons.i18n import _

from adhocracy import config
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


def get_sorted_categories(instance):
    SORTED_LIST = config.get_list('adhocracy.urbanliving.category_list',
                                    default=[], cast=int)

    categories = model.CategoryBadge.all_q(instance=instance,
                                           visible_only=True)\
        .filter(model.CategoryBadge.id.in_(SORTED_LIST)).all()
    #categories = filter(lambda c: len(c.children) == 0, categories)
    return sorted(categories, key=lambda c: SORTED_LIST.index(c.id))
