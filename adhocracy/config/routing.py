"""Routes configuration

The more specific and detailed routes should be defined first so they
may take precedent over the more generic routes. For more information
refer to the routes manual at http://routes.groovie.org/docs/
"""
from pylons import config
from routes import Mapper

def make_map():
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
    
    map.connect('/openid/{action}', controller='openidauth')
    map.connect('/twitter/{action}', controller='twitteroauth')
    
    map.resource('user', 'user', member={'votes': 'GET',
                                         'delegations': 'GET',
                                         'proposals': 'GET',
                                         'issues': 'GET', 
                                         #'comments': 'GET',
                                         'votes': 'GET',
                                         'instances': 'GET',
                                         'watchlist': 'GET',
                                         'groupmod': 'GET',
                                         'kick': 'GET',
                                         'revert': 'GET',
                                         'reset': 'GET',
                                         'activate': 'GET',
                                         'resend': 'GET'},
                                collection={'complete': 'GET',
                                            'filter': 'GET'})
    
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
    
    map.resource('issue', 'issue', member={'proposals': 'GET', 
                                           'discussion': 'GET', 
                                           'activity': 'GET', 
                                           'delegations': 'GET',
                                           'ask_delete': 'GET'},
                                   collection={'filter': 'GET'})

    map.resource('proposal', 'proposal', member={'votes': 'GET', 
                                                 'delegations': 'GET', 
                                                 'activity': 'GET', 
                                                 'canonicals': 'GET',
                                                 'contributors': 'GET',
                                                 'alternatives': 'GET',
                                                 'ask_delete': 'GET',
                                                 'ask_adopt': 'GET',
                                                 'adopt': 'POST',
                                                 'tag': 'POST',
                                                 'untag': 'GET'},
                               collection={'filter': 'GET'})
    
    map.connect('/page/diff', controller='page', action='diff',
                conditions=dict(method=['GET']))
    map.connect('/page/{id}/{variant}-{text}/edit.{format}', controller='page', action='edit',
                conditions=dict(method=['GET']))
    map.connect('/page/{id}/{variant}-{text}/edit', controller='page', action='edit',
                conditions=dict(method=['GET']))
    map.connect('/page/{id}/{variant}/edit.{format}', controller='page', action='edit',
                conditions=dict(method=['GET']))
    map.connect('/page/{id}/{variant}/edit', controller='page', action='edit',
                conditions=dict(method=['GET']))
    map.connect('/page/{id}/edit.{format}', controller='page', action='edit',
                conditions=dict(method=['GET']))
    map.connect('/page/{id}/edit', controller='page', action='edit',
                conditions=dict(method=['GET']))
    map.connect('/page/{id}/ask_delete', controller='page', action='ask_delete',
                conditions=dict(method=['GET']))
    map.connect('/page/{id}/{variant};{text}.{format}', controller='page', action='show',
                conditions=dict(method=['GET']))
    map.connect('/page/{id}/{variant};{text}', controller='page', action='show',
                conditions=dict(method=['GET']))
    map.connect('/page/{id}/{variant}/{text}', controller='page', action='show',
                conditions=dict(method=['GET']))
    map.connect('/page/{id}/{variant}.{format}', controller='page', action='show',
                conditions=dict(method=['GET']))
    map.connect('/page/{id}/{variant}', controller='page', action='show',
                conditions=dict(method=['GET']))
    map.connect('/page/{id};{text}.{format}', controller='page', action='show',
                conditions=dict(method=['GET']))
    map.connect('/page/{id};{text}', controller='page', action='show',
                conditions=dict(method=['GET']))
    
    map.resource('page', 'page', member={'ask_delete': 'GET'})

    #map.connect('/adopted', controller='proposal', action='adopted')
    
    map.resource('comment', 'comment', member={'history': 'GET',
                                               'revert': 'GET',
                                               'ask_delete': 'GET'})
                                               
    map.resource('poll', 'poll', member={'vote': 'POST',
                                         'rate': 'POST',
                                         'votes': 'GET',
                                         'ask_delete': 'GET'})
    
    # not using REST since tags may contain dots, thus failing format detection. 
    map.connect('/tag', controller='tag', action='index')
    map.connect('/tag/autocomplete', controller='tag', action='autocomplete')
    map.connect('/tag/{id}', controller='tag', action='show')
    
    map.resource('delegation', 'delegation')
    #map.resource('delegations', 'delegation')
    
    map.connect('/d/{id}', controller='root', action='dispatch_delegateable')
    map.connect('/sitemap.xml', controller='root', action='sitemap_xml')
    map.connect('/robots.txt', controller='root', action='robots_txt')
    map.connect('/feed.rss', controller='root', action='index', format='rss')
    map.connect('/_queue_process', controller='root', action='process')
        
    map.connect('/search/filter', controller='search', action='filter')
    map.connect('/search', controller='search', action='query')
        
    map.connect('/instance/{id}_{x}x{y}.png', 
                controller='instance', action='icon')
    map.resource('instance', 'instance', member={'join': 'GET', 
                                                 'leave': 'POST',
                                                 'filter': 'GET',
                                                 'ask_leave': 'GET',
                                                 'ask_delete': 'GET',
                                                 'activity': 'GET'})
    
    map.connect('/static/{page_name}.html', controller='static', action='serve')

    map.connect('/{controller}/{action}')
    map.connect('/{controller}/{action}/{id}')

    return map
