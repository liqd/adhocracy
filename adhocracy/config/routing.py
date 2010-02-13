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
                                         'comments': 'GET',
                                         'votes': 'GET',
                                         'instances': 'GET',
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
                                           'delegations': 'GET'},
                                   collection={'filter': 'GET'})

    map.resource('proposal', 'proposal', member={'votes': 'GET', 
                                                 'delegations': 'GET', 
                                                 'activity': 'GET', 
                                                 'canonicals': 'GET',
                                                 'alternatives': 'GET',
                                                 'ask_adopt': 'GET',
                                                 'adopt': 'POST'},
                               collection={'filter': 'GET'})
    
    map.connect('/adopted', controller='proposal', action='adopted')
    
    map.resource('comment', 'comment', member={'history': 'GET',
                                               'revert': 'GET'})
                                               
    map.resource('poll', 'poll', member={'vote': 'POST',
                                         'votes': 'GET',
                                         'ask_delete': 'GET'})
    
    map.resource('delegation', 'delegation')
    #map.resource('delegations', 'delegation')
    
    map.connect('/d/{id}', controller='root', action='dispatch_delegateable')
    map.connect('/sitemap.xml', controller='root', action='sitemap_xml')
    map.connect('/feed.rss', controller='root', action='index', format='rss')
    map.connect('/_queue_process', controller='root', action='process')
        
    map.connect('/search/filter', controller='search', action='filter')
    map.connect('/search', controller='search', action='query')
        
    map.connect('/adhocracies', controller='instance', action='index')
    map.connect('/instance/{id}_{x}x{y}.png', 
                controller='instance', action='icon')
    map.resource('instance', 'instance', member={'join': 'GET', 
                                                 'leave': 'GET',
                                                 'filter': 'GET',
                                                 'activity': 'GET'})
    
    map.connect('/page/{page_name}.html', controller='page', action='serve')

    map.connect('/{controller}/{action}')
    map.connect('/{controller}/{action}/{id}')

    return map
