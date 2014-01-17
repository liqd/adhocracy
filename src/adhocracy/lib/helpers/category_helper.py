from pylons.i18n import _

from adhocracy.lib import cache
from adhocracy.lib import logo
from adhocracy.lib.helpers import url as _url


def image_url(category, y, x=None):
    from adhocracy.lib.helpers import base_url
    if x is None:
        size = "%s" % y
    else:
        size = "%sx%s" % (x, y)
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
