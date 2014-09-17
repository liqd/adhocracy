import cgi

from pylons import tmpl_context as c
from pylons.i18n import _

from adhocracy import config
from adhocracy.lib import cache, logo
from adhocracy.lib.auth.authorization import has
from adhocracy.lib.helpers import url as _url
from adhocracy.lib.helpers.site_helper import CURRENT_INSTANCE
from adhocracy.model import Instance


def link(user, size=16, scope=None, show_badges=True):

    if user.delete_time:
        return _("%s (deleted user)") % user.name

    @cache.memoize('user_generic_link')
    def _generic_link(user, instance, size, scope):
        _url = u'<a href="%s" class="user">%s</a>' % (
            url(user), cgi.escape(user.name))
        return _url

    @cache.memoize('user_specific_link')
    def _specific_link(user, instance, size, scope, other,
                       show_badges):
        from adhocracy.lib import tiles
        url = _generic_link(user, instance, size, scope)
        badges = user.get_badges(instance)
        if show_badges and badges:
            url += u"<span class='badges'>" + \
                unicode(tiles.badge.badges(badges)) + "</span>"
        # FIXME: We removed user icons from the UI. What to do
        # with delegates?
        # if other and scope:
        #     dnode = democracy.DelegationNode(other, scope)
        #     for delegation in dnode.outbound():
        #         if delegation.agent == user:
        #             if show_icon:
        #                 icon = (
        #                     u'<img class="user_icon" width="16" height="16" '
        #                     'src="/img/icons/delegate_16.png" />')
        #             url += u'<a href="%s">%s</a>' % (entity_url(delegation),
        #                                              icon)
        return url

    return _specific_link(user, c.instance, size, scope, c.user, show_badges)


def url(user, instance=CURRENT_INSTANCE, **kwargs):
    '''
    Generate the url for a user. If *instance* is `None`, it will
    fallback to the current instance (taken from c.instance) for
    urls that are supposed to be in an instance subdomain, and ignore
    the instance argument for all other urls so they are always in the
    main domain.
    '''
    return _url.build(instance, 'user', user.user_name, **kwargs)


def logo_url(user, y, x=None):
    from adhocracy.lib.helpers import base_url
    size = "%s" % y if x is None else "%sx%s" % (x, y)
    filename = u"%s_%s.png" % (user.id, size)
    (path, mtime) = logo.path_and_mtime(user, fallback=logo.USER)
    return base_url(u'/user/%s' % filename, query_params={'t': str(mtime)})


def breadcrumbs(user, dashboard=False):
    from adhocracy.lib.helpers import base_url
    items = []
    if c.instance is not None:
        items.append(_url.link(_("Members"), base_url(u'/user')))
    elif has('user.index_all'):
        items.append(_url.link(_("Members"), base_url(u'/user/all')))
    if user is not None:
        items.append(_url.link(user.name, url(user)))
    if dashboard:
        items.append(_url.link(_('Dashboard'), base_url('/user/dashboard')))
    return _url.root() + _url.BREAD_SEP.join(items)


def settings_breadcrumbs(user, member=None):
    """member is a dict with the keys 'name' and 'label'."""
    bc = breadcrumbs(user)
    bc += _url.BREAD_SEP + _url.link(_("Settings"),
                                     url(user, member="settings"))
    if member is not None:
        bc += _url.BREAD_SEP + _url.link(
            member['label'],
            url(user, member="settings/" + member['name']))
    return bc


def post_login_url(user):
    from adhocracy.lib.helpers import base_url
    url = config.get('adhocracy.post_login_url')
    if url is None:
        return base_url('/user/%s/dashboard' % user.user_name)

    instance = config.get('adhocracy.post_login_instance')
    if instance is None:
        return base_url(url)
    else:
        return base_url(url, Instance.find(instance))


def post_register_url(user):
    from adhocracy.lib.helpers import base_url

    url = config.get('adhocracy.post_register_url')
    if url is None:
        return base_url('/user/%s/dashboard' % user.user_name)

    instance = config.get('adhocracy.post_register_instance')
    if instance is None:
        return base_url(url)
    else:
        return base_url(url, Instance.find(instance))


def post_logout_url():
    from adhocracy.lib.helpers import base_url
    url = config.get('adhocracy.post_logout_url')
    if url is None:
        return base_url()

    instance = config.get('adhocracy.post_logout_instance')
    if instance is None:
        return base_url(url)
    else:
        return base_url(url, Instance.find(instance))


def can_change_password(user):
    if user._shibboleths:
        return config.get_bool('adhocracy.allow_password_change')
    else:
        return True


def activation_url():
    from adhocracy.lib.auth.csrf import url_token
    from adhocracy.lib.helpers import base_url
    return base_url('/user/%s/resend?%s' % (c.user.user_name, url_token()))
