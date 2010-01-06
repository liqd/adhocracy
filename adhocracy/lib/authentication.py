import logging

from repoze.who.plugins.basicauth import BasicAuthPlugin
from repoze.who.plugins.auth_tkt import AuthTktCookiePlugin
from repoze.who.plugins.sa import SQLAlchemyAuthenticatorPlugin, \
                                  SQLAlchemyUserMDPlugin
from repoze.who.plugins.friendlyform import FriendlyFormPlugin

from repoze.what.middleware import setup_auth as setup_what
from repoze.what.plugins.sql.adapters import SqlGroupsAdapter, SqlPermissionsAdapter

import adhocracy.model as model 
from authorization import InstanceGroupSourceAdapter

log = logging.getLogger(__name__)

def setup_auth(app, config):
    
    groupadapter = InstanceGroupSourceAdapter()
    #groupadapter.translations.update({'sections': 'groups'})
    permissionadapter = SqlPermissionsAdapter(model.Permission, 
                                              model.Group, 
                                              model.meta.Session)
    #permissionadapter.translations.update(permission_translations)
    
    group_adapters = {'sql_auth': groupadapter}
    permission_adapters = {'sql_auth': permissionadapter}
        
    basicauth = BasicAuthPlugin('Adhocracy HTTP Authentication')
    auth_tkt = AuthTktCookiePlugin('41d207498d3812741e27c6441760ae494a4f9fbf', cookie_name='adhocracy_login')
        
    form = FriendlyFormPlugin(
            '/login',
            '/user/perform_login',
            '/user/post_login',
            '/logout',
            '/user/post_logout',
            login_counter_name='_login_tries',
            rememberer_name='auth_tkt')
    
    sqlauth = SQLAlchemyAuthenticatorPlugin(model.User, model.meta.Session)
    sql_user_md = SQLAlchemyUserMDPlugin(model.User, model.meta.Session)
            
    identifiers = [('form', form),('basicauth', basicauth), ('auth_tkt', auth_tkt)]
    authenticators = [('sqlauth', sqlauth)]
    challengers = [('form', form), ('basicauth', basicauth)]
    mdproviders = [('sql_user_md', sql_user_md)]
    
    log_stream = None
    #log_stream = sys.stdout
    
    return setup_what(app, group_adapters, permission_adapters, 
                      identifiers=identifiers, 
                      authenticators=authenticators,
                      challengers=challengers,
                      mdproviders=mdproviders,
                      log_stream = log_stream,
                      log_level = logging.DEBUG,
                      skip_authentication=config.get('skip_authentication'))