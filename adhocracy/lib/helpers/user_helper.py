import cgi

from pylons import tmpl_context as c
from pylons.i18n import _

from adhocracy.lib import cache
from adhocracy.lib.helpers import url as _url


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
        badges = [b for b in user.badges if b.instance is None
                  or b.instance is instance]
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


def url(user, instance=None, **kwargs):
    '''
    Generate the url for a user. If *instance* is `None`, it will
    fallback to the current instance (taken from c.instance) for
    urls that are supposed to be in an instance subdomain, and ignore
    the instance argument for all other urls so they are always in the
    main domain.
    '''
    @cache.memoize('user_url')
    def url_(user, instance, **kwargs):
        return _url.build(instance, 'user', user.user_name, **kwargs)

    # Allow only some user urls to be in an instance
    member = kwargs.get('member', None)
    if member in ['votes', 'delegations', 'proposals', 'groupmod',
                  'ban', 'unban', 'filter']:
        if instance is None:
            instance = c.instance

    return url_(user, instance, **kwargs)


@cache.memoize('user_bc')
def bc_entity(user):
    return _url.BREAD_SEP + _url.link(user.name, url(user))


def breadcrumbs(user):
    bc = _url.root()
    bc += _url.link(_("Users"), u'/user')
    if user is not None:
        bc += bc_entity(user)
    return bc
