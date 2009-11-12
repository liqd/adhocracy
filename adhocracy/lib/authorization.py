import logging

from pylons import config, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
from pylons.i18n import _

from repoze.what.predicates import has_permission as what_has_permission
from repoze.what.adapters import BaseSourceAdapter, SourceError
from repoze.what.plugins.sql.adapters import SqlGroupsAdapter

import adhocracy.model as model 
import karma 
import democracy
import helpers as h

log = logging.getLogger(__name__)


class InstanceGroupSourceAdapter(SqlGroupsAdapter):
    
    def __init__(self, *args, **kwargs):
        super(InstanceGroupSourceAdapter, self).__init__(model.Group, model.User, model.meta.Session)
        self.is_writable = False
        
    def _get_section_items(self, section):
        group = model.Group.by_code(section)
        users = []
        for membership in group.memberships: 
            if not membership.instance:
                users.append(membership.user)
            elif model.filter.has_instance() and \
                membership.instance == model.filter.get_instance():
                users.append(membership.user)
        return set(map(lambda u: u.user_name, users))

    def _get_item_as_row(self, item_name):
        user = model.User.find(item_name, instance_filter=False)
        if not user:
            raise SourceError("No such user: %s" % item_name)
        return user
        
        
class has_permission(what_has_permission):
    """
    This modified version of ``repoze.what``'s ``has_permission`` will apply ``Anonymous`` 
    rights to any user making requests. This allows to call ``has_permission`` on methods
    even when they are not protected, thus making the authorization system more 
    configurable.
    
    *WARNING*: This does not include authorizations that are subject to Karma thresholds. 
    """    
    def evaluate(self, environ, credentials):
        try:
            super(has_permission, self).evaluate(environ, credentials)
        except Exception, e:
            anonymous = model.Group.by_code(model.Group.CODE_ANONYMOUS)
            if anonymous:
                for perm in anonymous.permissions:
                    if perm.permission_name == self.permission_name:
                        return
            raise e 
        
def on_delegateable(delegateable, permission_name, allow_creator=True):
    """
    Check if a user can perform actions protected by the given permission on 
    the given delegateable. If ``allow_creator`` is set, allow the context user
    to perform all actions if she is the creator of ``delegateable``
    """
    if allow_creator and delegateable and c.user and c.user == delegateable.creator:
        return True
    if c.user and (c.user.has_permission('instance.admin') or c.user.has_permission('global.admin')):
        return True
    if c.user and c.user.has_permission(permission_name):
        if karma.user_score(c.user) >= karma.threshold.limit(permission_name):
            return True
    return False

def on_comment(comment, permission_name, allow_creator=True):
    """
    Check if a user can perform actions protected by the given permission on 
    the given comment. Equivalent to ``on_delegateable``. 
    """
    res = on_delegateable(comment.topic, permission_name, allow_creator=False)
    if c.user and c.user == comment.creator and allow_creator:
        return True
    return res

def require_delegateable_perm(delegateable, permission_name):
    """ If permission is not present, show a warning page. """
    if not on_delegateable(delegateable, permission_name):
        h.flash(karma.threshold.message(permission_name))
        if not delegateable:
            delegateable = c.instance.root
        redirect_to('/d/%s' % str(delegateable.id))
        
def require_motion_perm(motion, permission_name, enforce_immutability=True):
    """ If permission is not present, show a warning page. """
    require_delegateable_perm(motion, permission_name)
    if motion and not democracy.State(motion).motion_mutable and enforce_immutability:
        h.flash(h.immutable_motion_message())
        redirect_to('/motion/%s' % str(motion.id))

def require_comment_perm(comment, permission_name, enforce_immutability=True):
    """ If permission is not present, show a warning page. """
    if not on_comment(comment, permission_name):
        h.flash(karma.threshold.message(permission_name))
        redirect_to('/comment/r/%s' % comment.id)
    if not democracy.is_comment_mutable(comment) and enforce_immutability:
        h.flash(h.immutable_motion_message())
        redirect_to('/comment/r/%s' % comment.id)


    