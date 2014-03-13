from pylons.i18n import _

from adhocracy import config
from adhocracy import static
from adhocracy.lib import logo
from adhocracy.lib.helpers import url as _url


def url(instance, member=None, format=None, **kwargs):
    return _url.build(instance, 'instance', instance.key,
                      member=member, format=format, **kwargs)


def logo_url(instance, y, x=None):
    size = "%s" % y if x is None else "%sx%s" % (x, y)
    filename = "%s_%s.png" % (instance.key, size)
    (path, mtime) = logo.path_and_mtime(instance, fallback=logo.INSTANCE)
    return _url.build(instance, 'instance', filename, query={'t': str(mtime)})


def breadcrumbs(instance=None):
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


def area_title(identifier):
    """identifier is typically the value of c.active_subheader_nav"""
    if identifier == 'proposals':
        return _("Proposals")
    elif identifier == 'milestones':
        return _("Milestones")
    elif identifier == 'norms':
        return _("Norms")
    elif identifier == 'category':
        return _("Categories")
    elif identifier == 'members':
        return _("Members")
    else:
        if config.get_bool('adhocracy.wording.intro_for_overview'):
            return _(u"Intro")
        else:
            return _(u"Overview")


def need_stylesheet(instance):
    stylesheets = config.get_list('adhocracy.instance_stylesheets')
    themes = config.get_list('adhocracy.instance_themes')
    if instance is not None and instance.key in stylesheets:
        return static.instance_stylesheet(instance.key).need()
    elif (instance is not None and instance.theme in themes and
            instance.is_authenticated):
        return static.instance_theme(instance.theme).need()
    else:
        return static.style.need()
