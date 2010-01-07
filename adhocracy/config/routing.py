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
    map.connect('/register', controller='user', action='create')
    map.connect('/login', controller='user', action='login')
    map.connect('/logout', controller='user', action='logout')
        
    map.connect('/users', controller='user', action='index')
    map.connect('/user/post_logout', controller='user', action='post_logout')
    map.connect('/user/post_login', controller='user', action='post_login')
    map.connect('/user/perform_login', controller='user', action='perform_login')
    map.connect('/user/reset/{id}', controller='user', action='reset_code')
    map.connect('/user/reset', controller='user', action='reset')
    map.connect('/user/complete', controller='user', action='autocomplete')
    map.connect('/user/edit/{id}', controller='user', action='edit')
    map.connect('/user/{id}/votes', controller='user', action='votes')
    map.connect('/user/{id}/delegations', controller='user', action='delegations')
    map.connect('/user/{id}/proposals', controller='user', action='proposals')
    map.connect('/user/{id}/groupmod', controller='user', action='groupmod')
    map.connect('/user/{id}/kick', controller='user', action='kick')
    map.connect('/user/{id}.{format}', controller='user', action='view')
    map.connect('/user/{id}', controller='user', action='view', format='html')
    map.connect('/openid/{action}', controller='openidauth')
    map.connect('/twitter/{action}', controller='twitteroauth')
    
    map.connect('/issue/create', controller='issue', action='create')
    map.connect('/issue/{action}/{id}', controller='issue')
    map.connect('/issue/{id}.{format}', controller='issue', action='view')
    map.connect('/issue/{id}', controller='issue', action='view', format='html')
    
    map.connect('/proposal/create', controller='proposal', action='create')
    map.connect('/proposal/{id}/votes', controller='proposal', action='votes')
    map.connect('/proposal/{action}/{id}', controller='proposal')
    map.connect('/proposal/{id}.{format}', controller='proposal', action='view')
    map.connect('/proposal/{id}', controller='proposal', action='view', format='html')
    
    map.connect('/polls', controller='poll', action='index')
    
    map.connect('/comment/create', controller='comment', action='create')
    map.connect('/comment/edit/{id}', controller='comment', action='edit')
    map.connect('/comment/delete/{id}', controller='comment', action='delete')
    map.connect('/comment/{id}/history', controller='comment', action='history')
    map.connect('/comment/{id}/revert', controller='comment', action='revert')
    map.connect('/comment/r/{id}', controller='comment', action='redirect')
    map.connect('/comment/{id}', controller='comment', action='view')
    
    map.connect('/karma/give', controller='karma', action='give', format='html')
    map.connect('/karma/give.json', controller='karma', action='give', format='json')
    
    map.connect('/category/create', controller='category', action='create')
    map.connect('/category/{action}/{id}', controller='category')
    map.connect('/category/{id}.{format}', controller='category', action='view')
    map.connect('/category/{id}', controller='category', action='view', format='html')
    
    map.connect('/delegation/create', controller='delegation', action='create')
    map.connect('/delegation/graph.dot', controller='delegation', action='graph')
    map.connect('/delegation/revoke/{id}', controller='delegation', action='revoke')
    map.connect('/delegation/user/{id}', controller='delegation', action='user')
    map.connect('/delegation/{id}', controller='delegation', action='review')
    
    map.connect('/d/{id}', controller='root', action='dispatch_delegateable')
    map.connect('/sitemap.xml', controller='root', action='sitemap_xml')
    map.connect('/feed.rss', controller='root', action='index', format='rss')
    map.connect('/_queue_process', controller='root', action='process')
        
    map.connect('/search', controller='search', action='query')
        
    map.connect('/adhocracies', controller='instance', action='index')
    map.connect('/instance/create', controller='instance', action='create')
    map.connect('/instance/{key}/join', controller='instance', action='join')
    map.connect('/instance/{key}/leave', controller='instance', action='leave')
    map.connect('/instance/header/{key}.png', controller='instance', action='header')
    map.connect('/instance/icon/{key}-{x}x{y}.png', controller='instance', action='icon')
    map.connect('/instance/{action}/{key}', controller='instance')
    map.connect('/instance/{key}.rss', controller='instance', action='view', format='rss')
    map.connect('/instance/{key}', controller='instance', action='view', format='html')
    
    map.connect('/page/{page_name}.html', controller='page', action='serve')

    map.connect('/{controller}/{action}')
    map.connect('/{controller}/{action}/{id}')

    return map
