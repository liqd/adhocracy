from adhocracy.lib import logo


def image_url(category, y, x=None):
    from adhocracy.lib.helpers import base_url
    if x is None:
        size = "%s" % y
    else:
        size = "%sx%s" % (x, y)
    filename = u"%s_%s.png" % (category.title, size)
    (path, mtime) = logo.path_and_mtime(category)
    return base_url(u'/category/%s' % filename, query_params={'t': str(mtime)})
