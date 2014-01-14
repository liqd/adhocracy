from pylons.i18n import _

from adhocracy.lib import logo
from adhocracy.lib.helpers import url as _url


def url(instance, member=None, format=None, **kwargs):
    return _url.build(instance, 'instance', instance.key,
                      member=member, format=format, **kwargs)


def icon_url(instance, y, x=None):
    if x is None:
        size = "%s" % y
    else:
        size = "%sx%s" % (x, y)
    filename = "%s_%s.png" % (instance.key, size)
    (path, mtime) = logo.path_and_mtime(instance)
    return _url.build(instance, 'instance', filename, query={'t': str(mtime)})


def breadcrumbs(instance):
    bc = _url.root()
    return bc


def settings_breadcrumbs(instance, member=None):
    """member is a dict with the keys 'name' and 'label'."""
    bc = breadcrumbs(instance)
    bc += _url.link(_("Settings"), url(instance, member="settings"))
    if member is not None:
        bc += _url.BREAD_SEP + _url.link(
            member['label'],
            url(instance, member="settings/" + member['name']))
    return bc
