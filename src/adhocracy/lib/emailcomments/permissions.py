from repoze.what.middleware import AuthorizationMetadata
from repoze.what.plugins.sql.adapters import SqlPermissionsAdapter
from adhocracy import model
from adhocracy.lib.auth.authorization import InstanceGroupSourceAdapter
import logging

log = logging.getLogger(__name__)


def setup_perm(environ, user):
    '''
    Set permissions for replying user. This is a short authorization
    for emailcomments. It contains some functions of
    lib/auth/authentication: setup_auth.
    Though the adapters must be passed from here to AuthorizationMetadata
    directly to setup authorization for the user. Logging in is neither
    required nor useful so a modified quick-auth comes in handy.
    '''

    identity = {'repoze.who.userid': str(user.user_name)}

    groupadapter = InstanceGroupSourceAdapter()
    permissionadapter = SqlPermissionsAdapter(model.Permission,
                                              model.Group,
                                              model.meta.Session)
    group_adapters = {'sql_auth': groupadapter}
    permission_adapters = {'sql_auth': permissionadapter}

    get_perm = AuthorizationMetadata(group_adapters=group_adapters,
        permission_adapters=permission_adapters)
    AuthorizationMetadata.add_metadata(get_perm, environ, identity)
