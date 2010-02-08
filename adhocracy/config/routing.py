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
        
    map.connect('/issue/create', controller='issue', action='create')
    map.connect('/issue/{id}/proposals', controller='issue', action='proposals')
    map.connect('/issue/{id}/activity', controller='issue', action='activity')
    map.connect('/issue/{id}/delegations', controller='issue', action='delegations')
    map.connect('/issue/{action}/{id}', controller='issue')
    map.connect('/issue/{id}.{format}', controller='issue', action='view')
    map.connect('/issue/{id}', controller='issue', action='view', format='html')
    
    map.connect('/proposal/create', controller='proposal', action='create')
    map.connect('/adopted', controller='proposal', action='adopted')
    map.connect('/proposal/{id}/votes', controller='proposal', action='votes')
    map.connect('/proposal/{id}/activity', controller='proposal', action='activity')
    map.connect('/proposal/{id}/delegations', controller='proposal', action='delegations')
    map.connect('/proposal/{id}/canonicals', controller='proposal', action='canonicals')
    map.connect('/proposal/{action}/{id}', controller='proposal')
    map.connect('/proposal/{id}.{format}', controller='proposal', action='view')
    map.connect('/proposal/{id}', controller='proposal', action='view', format='html')
    
    map.connect('/poll/create/{id}', controller='poll', action='create')
    map.connect('/poll/{id}/abort', controller='poll', action='abort')
    map.connect('/poll/{id}/votes', controller='poll', action='votes')
    map.connect('/poll/{id}', controller='poll', action='view')
    map.connect('/polls', controller='poll', action='index')
    
    
    map.resource('comment', 'comment', member={'history': 'GET',
                                               'revert': 'GET'})
    
    map.connect('/karma/give', controller='karma', action='give', format='html')
    map.connect('/karma/give.json', controller='karma', action='give', format='json')
    
    map.resource('delegation', 'delegation')
    #map.resource('delegations', 'delegation')
    
    map.connect('/d/{id}', controller='root', action='dispatch_delegateable')
    map.connect('/sitemap.xml', controller='root', action='sitemap_xml')
    map.connect('/feed.rss', controller='root', action='index', format='rss')
    map.connect('/_queue_process', controller='root', action='process')
        
    map.connect('/search/filter', controller='search', action='filter')
    map.connect('/search', controller='search', action='query')
        
    map.connect('/adhocracies', controller='instance', action='index')
    
    map.connect('/instance/create', controller='instance', action='create')
    map.connect('/instance/{key}/join', controller='instance', action='join')
    map.connect('/instance/{key}/leave', controller='instance', action='leave')
    map.connect('/instance/{key}/filter', controller='instance', action='filter')
    map.connect('/instance/{key}/activity', controller='instance', action='activity')
    map.connect('/instance/header/{key}.png', controller='instance', action='header')
    map.connect('/instance/icon/{key}-{x}x{y}.png', controller='instance', action='icon')
    map.connect('/instance/{action}/{key}', controller='instance')
    map.connect('/instance/{key}.rss', controller='instance', action='view', format='rss')
    map.connect('/instance/{key}', controller='instance', action='view', format='html')
        
    map.connect('/page/{page_name}.html', controller='page', action='serve')

    map.connect('/{controller}/{action}')
    map.connect('/{controller}/{action}/{id}')

    return map
