import logging

from repoze.who.plugins.basicauth import BasicAuthPlugin
from repoze.who.plugins.sa import SQLAlchemyAuthenticatorPlugin, \
                                  SQLAlchemyUserMDPlugin
from repoze.who.plugins.friendlyform import FriendlyFormPlugin

from repoze.what.middleware import setup_auth as setup_what
from repoze.what.plugins.sql.adapters import SqlPermissionsAdapter

import adhocracy.model as model
from authorization import InstanceGroupSourceAdapter
from instance_auth_tkt import InstanceAuthTktCookiePlugin

from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
import repoze.who.plugins.sa

log = logging.getLogger(__name__)

class _EmailBaseSQLAlchemyPlugin(object):
    default_translations = {'user_name': "user_name", 'email': 'email', 'validate_password': "validate_password"}

    def get_user(self, login):
        login_type = u'email' if u'@' in login else u'user_name'
        login_attr = getattr(self.user_class, self.translations[login_type])
        query = self.dbsession.query(self.user_class)
        query = query.filter(login_attr == login)

        try:
            return query.one()
        except (NoResultFound, MultipleResultsFound):
            # As recommended in the docs for repoze.who, it's important to
            # verify that there's only _one_ matching userid.
            return None

class EmailSQLAlchemyAuthenticatorPlugin(_EmailBaseSQLAlchemyPlugin,
          repoze.who.plugins.sa.SQLAlchemyAuthenticatorPlugin):
              
    def authenticate(self, environ, identity):
        if not ("login" in identity and "password" in identity):
            return None
        
        user = self.get_user(identity['login'])
        
        if user:
            validator = getattr(user, self.translations['validate_password'])
            if validator(identity['password']):
                return user.user_name           #this is just a quick fix
                #return identity['login']
                
class EmailSQLAlchemyUserMDPlugin(_EmailBaseSQLAlchemyPlugin,
          repoze.who.plugins.sa.SQLAlchemyUserMDPlugin):
    pass
    

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
    auth_tkt = InstanceAuthTktCookiePlugin(
        '41d207498d3812741e27c6441760ae494a4f9fbf',
        cookie_name='adhocracy_login', timeout=86400 * 2,
        reissue_time=3600)

    form = FriendlyFormPlugin(
            '/login',
            '/perform_login',
            '/post_login',
            '/logout',
            '/post_logout',
            login_counter_name='_login_tries',
            rememberer_name='auth_tkt')
    
    sqlauth = EmailSQLAlchemyAuthenticatorPlugin(model.User, model.meta.Session)
    sql_user_md = SQLAlchemyUserMDPlugin(model.User, model.meta.Session)

    identifiers = [('form', form),
                   ('basicauth', basicauth),
                   ('auth_tkt', auth_tkt)]
    authenticators = [('sqlauth', sqlauth), ('auth_tkt', auth_tkt)]
    challengers = [('form', form), ('basicauth', basicauth)]
    mdproviders = [('sql_user_md', sql_user_md)]

    log_stream = None
    #log_stream = sys.stdout

    return setup_what(app, group_adapters, permission_adapters,
                      identifiers=identifiers,
                      authenticators=authenticators,
                      challengers=challengers,
                      mdproviders=mdproviders,
                      log_stream=log_stream,
                      log_level=logging.DEBUG,
                      # kwargs passed to repoze.who.plugins.testutils:
                      skip_authentication=config.get('skip_authentication'),
                      remote_user_key='HTTP_REMOTE_USER')
