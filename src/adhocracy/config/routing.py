"""Routes configuration

The more specific and detailed routes should be defined first so they
may take precedent over the more generic routes. For more information
refer to the routes manual at http://routes.groovie.org/docs/
"""
from routes import Mapper


def make_map(config):
    """Create, configure and return the routes Mapper"""
    map = Mapper(directory=config['pylons.paths']['controllers'],
                 always_scan=config['debug'])
    map.minimization = False

    # The ErrorController route (handles 404/500 error pages); it should
    # likely stay at the top, ensuring it can always be resolved
    map.connect('/error/{action}', controller='error')
    map.connect('/error/{action}/{id}', controller='error')

    # CUSTOM ROUTES HERE
    map.connect('/', controller='root', action='index')
    map.connect('/index{.format}', controller='root', action='index')

    map.connect('/openid/{action}', controller='openidauth')
    map.connect('/twitter/{action}', controller='twitteroauth')

    map.connect('/user/all', controller='user',
                action='all', conditions=dict(method=['GET']))
    map.connect('/user/{id}/badges', controller='user',
                action='badges', conditions=dict(method=['GET']))
    map.connect('/user/{id}/badges', controller='user',
                action='update_badges', conditions=dict(method=['POST']))
    map.connect('/user/{id}/dashboard', controller='user',
                action='dashboard')
    map.connect('/user/{id}/dashboard_proposals', controller='user',
                action='dashboard_proposals')
    map.connect('/user/{id}/dashboard_pages', controller='user',
                action='dashboard_pages')
    map.connect('/welcome/{id}/{token}', controller='user',
                action='welcome')
    map.resource('user', 'user', member={'votes': 'GET',
                                         'delegations': 'GET',
                                         'votes': 'GET',
                                         'instances': 'GET',
                                         'watchlist': 'GET',
                                         'groupmod': 'GET',
                                         'ban': 'GET',
                                         'unban': 'GET',
                                         'ask_delete': 'GET',
                                         'revert': 'GET',
                                         'reset': 'GET',
                                         'activate': 'GET',
                                         'resend': 'GET',
                                         'set_password': 'POST'},
                 collection={'complete': 'GET',
                             'filter': 'GET'})

    # TODO work this into a complete subcontroller.
    map.connect('/user/{id}/message.{format}', controller='message',
                action='create',
                conditions=dict(method=['POST', 'PUT']))
    map.connect('/user/{id}/message', controller='message', action='create',
                conditions=dict(method=['POST', 'PUT']))
    map.connect('/user/{id}/message/new.{format}', controller='message',
                action='new',
                conditions=dict(method=['GET']))
    map.connect('/user/{id}/message/new', controller='message', action='new',
                conditions=dict(method=['GET']))

    map.connect('/message/new', controller='massmessage', action='new')
    map.connect('/message/preview', controller='massmessage', action='preview')
    map.connect('/message/create', controller='massmessage', action='create')


    map.connect('/register', controller='user', action='new')
    map.connect('/login', controller='user', action='login')
    map.connect('/logout', controller='user', action='logout')
    map.connect('/post_logout', controller='user', action='post_logout')
    map.connect('/post_login', controller='user', action='post_login')
    map.connect('/perform_login', controller='user', action='perform_login')
    map.connect('/reset', controller='user', action='reset_form',
                conditions=dict(method=['GET']))
    map.connect('/reset', controller='user', action='reset_request',
                conditions=dict(method=['POST']))

    #map.connect('/proposal/{id}/badges', controller='proposal',
                #action='badges', conditions=dict(method=['GET']))
    #map.connect('/proposal/{id}/badges', controller='proposal',
                #action='update_badges', conditions=dict(method=['POST']))

    map.resource('proposal', 'proposal', member={'votes': 'GET',
                                                 'delegations': 'GET',
                                                 'activity': 'GET',
                                                 'alternatives': 'GET',
                                                 'ask_delete': 'GET',
                                                 'ask_adopt': 'GET',
                                                 'adopt': 'POST',
                                                 'tag': 'POST',
                                                 'untag': 'GET',
                                                 'badges': 'GET',
                                                 'update_badges': 'POST',
                                                 'history': 'GET'},
                 collection={'filter': 'GET'})
    map.connect('/proposal/{proposal_id}/{selection_id}/details{.format}',
                controller='selection',
                action='details')

    map.resource('implementation', 'implementation', controller='selection',
                 member={'ask_delete': 'GET'},
                 collection={'include': 'GET',
                             'propose': 'GET'},
                 parent_resource=dict(member_name='proposal',
                                      collection_name='proposal'))

    map.connect('/page/diff', controller='page', action='diff',
                conditions=dict(method=['GET']))
    map.connect('/page/{id}/{variant}/history{.format}',
                controller='page',
                action='history',
                conditions=dict(method=['GET']))
    map.connect('/page/{id}/history{.format}',
                controller='page',
                action='history',
                conditions=dict(method=['GET']),
                )
    map.connect('/page/{id}/{variant}/branch',
                controller='page',
                action='edit',
                branch=True,
                conditions=dict(method=['GET']))
    map.connect('/page/{id}/{variant}/ask_purge',
                controller='page', action='ask_purge',
                conditions=dict(method=['GET']))
    map.connect('/page/{id}/{variant}/purge',
                controller='page',
                action='purge',
                conditions=dict(method=['POST', 'DELETE']))
    map.connect('/page/{id};{text}/ask_purge_history',
                controller='page', action='ask_purge_history',
                conditions=dict(method=['GET']))
    map.connect('/page/{id};{text}/purge_history',
                controller='page',
                action='purge_history',
                conditions=dict(method=['POST', 'DELETE']))
    map.connect('/page/{id}/{variant}/edit.{format}',
                controller='page',
                action='edit',
                conditions=dict(method=['GET']))
    map.connect('/page/{id}/{variant}/edit', controller='page', action='edit',
                conditions=dict(method=['GET']))
    map.connect('/page/{id}/edit.{format}', controller='page', action='edit',
                conditions=dict(method=['GET']))
    map.connect('/page/{id}/branch', controller='page', action='edit',
                branch=True,
                conditions=dict(method=['GET']))
    map.connect('/page/{id}/edit', controller='page', action='edit',
                conditions=dict(method=['GET']))
    map.connect('/page/{id}/ask_delete', controller='page',
                action='ask_delete',
                conditions=dict(method=['GET']))
    map.connect('/page/{id}/{variant};{text}.{format}', controller='page',
                action='show',
                conditions=dict(method=['GET']))
    map.connect('/page/{id}/{variant};{text}/branch', controller='page',
                action='edit', branch=True,
                conditions=dict(method=['GET']))
    map.connect('/page/{id}/{variant};{text}', controller='page',
                action='show',
                conditions=dict(method=['GET']))
    map.connect('/page/{id}/{variant}.{format}', controller='page',
                action='show',
                conditions=dict(method=['GET']))
    map.connect('/page/{id}/{variant}', controller='page', action='show',
                conditions=dict(method=['GET']))
    map.connect('/page/{id};{text}.{format}', controller='page', action='show',
                conditions=dict(method=['GET']))
    map.connect('/page/{id};{text}/branch', controller='page', action='edit',
                branch=True,
                conditions=dict(method=['GET']))
    map.connect('/page/{id};{text}', controller='page', action='show',
                conditions=dict(method=['GET']))

    map.resource('page', 'page', member={'ask_delete': 'GET'})

    #map.connect('/adopted', controller='proposal', action='adopted')

    map.resource('comment', 'comment', member={'history': 'GET',
                                               'revert': 'GET',
                                               'purge_history': 'GET',
                                               'ask_delete': 'GET'})

    map.connect('/comment/form/edit/{id}', controller='comment',
                action='edit_form')
    map.connect('/comment/form/create/{topic}', controller='comment',
                action='create_form', variant=None)
    map.connect('/comment/form/reply/{id}', controller='comment',
                action='reply_form')

    map.resource('milestone', 'milestone', member={'ask_delete': 'GET'})

    map.connect('/poll/{id}/rate{.format}', controller='poll', action='rate',
                conditions=dict(method=['GET', 'POST']))

    map.connect('/poll/{id}/widget{.format}', controller='poll',
                action='widget', conditions=dict(method=['GET', 'POST']))

    map.connect('/poll/{id}/vote{.format}', controller='poll', action='vote',
                conditions=dict(method=['GET', 'POST']))

    map.resource('poll', 'poll', member={'votes': 'GET',
                                         'ask_delete': 'GET',
                                         'widget': 'GET'})

    map.connect('/badge', controller='badge', action='index',
                conditions=dict(method=['GET']))
    map.connect('/badge/{badge_type}/add', controller='badge',
                action='add', conditions=dict(method=['GET']))
    map.connect('/badge/{badge_type}/add', controller='badge',
                action='create', conditions=dict(method=['POST']))
    map.connect('/badge/edit/{id}', controller='badge',
                action="edit", conditions=dict(method=['GET']))
    map.connect('/badge/edit/{id}',
                controller='badge', action="update",
                conditions=dict(method=['POST']))

    # not using REST since tags may contain dots, thus failing format
    # detection.
    map.connect('/tag', controller='tag', action='index',
                conditions=dict(method=['GET']))
    map.connect('/tag', controller='tag', action='create',
                conditions=dict(method=['POST']))
    map.connect('/tag/autocomplete', controller='tag', action='autocomplete')
    map.connect('/untag', controller='tag', action='untag')
    map.connect('/untag_all', controller='tag', action='untag_all')
    map.connect('/tag/{id}', controller='tag', action='show')

    map.resource('delegation', 'delegation')
    #map.resource('delegations', 'delegation')

    map.connect('/d/{id}', controller='root', action='dispatch_delegateable')
    map.connect('/sitemap.xml', controller='root', action='sitemap_xml')
    map.connect('/robots.txt', controller='root', action='robots_txt')
    map.connect('/feed.rss', controller='root', action='index', format='rss')
    map.connect('/tutorials', controller='root', action='tutorials')

    map.connect('/search/filter', controller='search', action='filter')
    map.connect('/search', controller='search', action='query')

    map.connect('/abuse/report', controller='abuse', action='report')
    map.connect('/abuse/new', controller='abuse', action='new')

    map.connect('/instance/{id}_{x}x{y}.png',
                controller='instance', action='icon')
    map.connect('/instance/{id}_{y}.png',
                controller='instance', action='icon')
    map.connect('/instance/{id}/settings',
                controller='instance', action='settings_general',
                conditions=dict(method=['GET']))
    map.connect('/instance/{id}/settings',
                controller='instance', action='settings_general_update',
                conditions=dict(method=['PUT']))
    map.connect('/instance/{id}/settings/appearance',
                controller='instance', action='settings_appearance',
                conditions=dict(method=['GET']))
    map.connect('/instance/{id}/settings/appearance',
                controller='instance', action='settings_appearance_update',
                conditions=dict(method=['PUT']))
    map.connect('/instance/{id}/settings/contents',
                controller='instance', action='settings_contents',
                conditions=dict(method=['GET']))
    map.connect('/instance/{id}/settings/contents',
                controller='instance', action='settings_contents_update',
                conditions=dict(method=['PUT']))
    map.connect('/instance/{id}/settings/voting',
                controller='instance', action='settings_voting',
                conditions=dict(method=['GET']))
    map.connect('/instance/{id}/settings/voting',
                controller='instance', action='settings_voting_update',
                conditions=dict(method=['PUT']))
    map.connect('/instance/{id}/settings/badges',
                controller='instance', action='settings_badges',
                conditions=dict(method=['GET']))
    map.connect('/instance/{id}/settings/badges',
                controller='instance', action='settings_badges_update',
                conditions=dict(method=['PUT']))
    map.connect('/instance/{id}/settings/badges/{badge_type}/add',
                controller='instance',
                action='settings_badges_add', conditions=dict(method=['GET']))
    map.connect('/instance/{id}/settings/badges/{badge_type}/add',
                controller='instance',
                action='settings_badges_create',
                conditions=dict(method=['POST']))
    map.connect('/instance/{id}/settings/badges/edit/{badge_id}',
                controller='instance',
                action="settings_badges_edit", conditions=dict(method=['GET']))
    map.connect('/instance/{id}/settings/badges/edit/{badge_id}',
                controller='instance', action="settings_badges_update",
                conditions=dict(method=['POST']))
    map.connect('/instance/{id}/settings/massmessage',
                controller='massmessage', action='new',
                conditions=dict(method=['GET']))
    map.connect('/instance/{id}/settings/massmessage',
                controller='massmessage', action='create',
                conditions=dict(method=['POST']))
    map.connect('/instance/{id}/settings/members_import',
                controller='instance', action='settings_members_import',
                conditions=dict(method=['GET']))
    map.connect('/instance/{id}/settings/members_import',
                controller='instance', action='settings_members_import_save',
                conditions=dict(method=['PUT', 'POST']))

    map.resource('instance', 'instance', member={'join': 'GET',
                                                 'leave': 'POST',
                                                 'filter': 'GET',
                                                 'ask_leave': 'GET',
                                                 'ask_delete': 'GET',
                                                 'style': 'GET',
                                                 'badges': 'GET',
                                                 'update_badges': 'POST',
                                                 'activity': 'GET'})

    map.connect('/stats/', controller='stats')

    # API
    map.connect('/api/{action}', controller='api')
    map.connect('/admin', controller='admin', action="index")
    map.connect('/admin/users/import', controller='admin',
                action="user_import", conditions=dict(method=['POST']))
    map.connect('/admin/users/import', controller='admin',
                action="user_import_form", conditions=dict(method=['GET']))
    map.connect('/admin/export',
                controller='admin', action='export_dialog')
    map.connect('/admin/export/do',
                controller='admin', action='export_do')
    map.connect('/admin/import',
                controller='admin', action='import_dialog')
    map.connect('/admin/import/do',
                controller='admin', action='import_do')

    map.connect('/static/', controller='static', action='index',
                conditions=dict(method=['GET', 'HEAD']))
    map.connect('/static/', controller='static', action='make_new',
                conditions=dict(method=['POST']))
    map.connect('/static/new', controller='static', action='new')
    map.connect('/static/{key}_{lang}',
                controller='static', action='edit',
                conditions=dict(method=['GET', 'HEAD']))
    map.connect('/static/{key}_{lang}',
                controller='static', action='update',
                conditions=dict(method=['POST']))
    map.connect('/static/{key}.{format}', controller='static',
                action='serve')

    map.connect('/{controller}/{action}')
    map.connect('/{controller}/{action}/{id}')

    return map
