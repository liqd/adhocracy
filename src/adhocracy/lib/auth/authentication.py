import logging

from repoze.who.plugins.basicauth import BasicAuthPlugin
from repoze.who.plugins.sa import SQLAlchemyAuthenticatorPlugin
from repoze.who.plugins.sa import SQLAlchemyUserMDPlugin
from repoze.who.plugins.friendlyform import FriendlyFormPlugin

from repoze.what.middleware import setup_auth as setup_what
from repoze.what.plugins.sql.adapters import SqlPermissionsAdapter

import adhocracy.model as model
from . import welcome
from authorization import InstanceGroupSourceAdapter
from instance_auth_tkt import InstanceAuthTktCookiePlugin

from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
import repoze.who.plugins.sa
from pylons import config

log = logging.getLogger(__name__)

def allowed_login_types():
    login = config.get('adhocracy.login_type', 'openid,username+password,email+password')
    login = login.split(',')
    return login


class _EmailBaseSQLAlchemyPlugin(object):
    default_translations = {'user_name': "user_name", 'email': 'email', 'validate_password': "validate_password"}

    def get_user(self, login, allow_name, allow_email):
        if allow_name:
            if allow_email:
                login_type = u'email' if u'@' in login else u'user_name'
            else:
                login_type = u'user_name'
        else:
            if allow_email:
                login_type = u'email'
            else:
                return None
        
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
            
        login_configuration = allowed_login_types()
        allow_name = 'username+password' in login_configuration
        allow_email = 'email+password' in login_configuration
        
        user = self.get_user(identity['login'], allow_name, allow_email)
        
        if user:
            validator = getattr(user, self.translations['validate_password'])
            if validator(identity['password']):
                return user.user_name
                
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
        config,
        config.get('adhocracy.auth.secret', config['beaker.session.secret']),
        cookie_name='adhocracy_login', timeout=86400 * 2,
        reissue_time=3600,
        secure=config.get('adhocracy.protocol', 'http') == 'https'
    )

    form = FriendlyFormPlugin(
            '/login',
            '/perform_login',
            '/post_login',
            '/logout',
            '/post_logout',
            login_counter_name='_login_tries',
            rememberer_name='auth_tkt',
            charset='utf-8'
    )
    
    sqlauth = EmailSQLAlchemyAuthenticatorPlugin(model.User, model.meta.Session)
    sql_user_md = SQLAlchemyUserMDPlugin(model.User, model.meta.Session)

    identifiers = [('form', form),
                   ('basicauth', basicauth),
                   ('auth_tkt', auth_tkt)]
    authenticators = [('sqlauth', sqlauth), ('auth_tkt', auth_tkt)]
    challengers = [('form', form), ('basicauth', basicauth)]
    mdproviders = [('sql_user_md', sql_user_md)]

    welcome.setup_auth(config, identifiers, authenticators)

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
