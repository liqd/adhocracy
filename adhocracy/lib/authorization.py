import logging

from pylons import config, tmpl_context as c
from pylons import request
from pylons.controllers.util import abort, redirect_to
from pylons.i18n import _

from sqlalchemy import and_, or_
from sqlalchemy.orm import eagerload

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
        q = model.meta.Session.query(model.User.user_name)
        q = q.join(model.Membership)
        q = q.join(model.Group)
        q = q.filter(model.Group.code==section)
        q = q.filter(or_(model.Membership.instance==None,
                         model.Membership.instance==model.filter.get_instance()))
        return q.all()
    
    def _find_sections(self, credentials):
        sections = list(super(InstanceGroupSourceAdapter, self)._find_sections(credentials))
        sections.append("Anonymous")
        return set(sections)

    def _get_item_as_row(self, item_name):
        q = model.meta.Session.query(model.User)
        q = q.filter(model.User.user_name==item_name)
        q = q.options(eagerload(model.User.memberships))
        try:
            return q.one()
        except Exception, e:
            log.debug(e)
            raise SourceError("No such user: %s" % item_name)
        
class has_permission(what_has_permission):
    """
    This modified version of ``repoze.what``'s ``has_permission`` will apply ``Anonymous`` 
    rights to any user making requests. This allows to call ``has_permission`` on methods
    even when they are not protected, thus making the authorization system more 
    configurable.
    
    *WARNING*: This does not include authorizations that are subject to Karma thresholds. 
    """    
    def evaluate(self, environ, credentials):
        if c.user:
            super(has_permission, self).evaluate(environ, credentials)
        else:
            anon_group = model.Group.by_code(model.Group.CODE_ANONYMOUS)
            for perm in anon_group.permissions:
                if perm.permission_name == self.permission_name:
                    return
            self.unmet()
        

def has_permission_bool(permission):
    p = has_permission(permission)
    return p.is_met(request.environ)
        
def on_delegateable(delegateable, permission_name, allow_creator=True):
    """
    Check if a user can perform actions protected by the given permission on 
    the given delegateable. If ``allow_creator`` is set, allow the context user
    to perform all actions if she is the creator of ``delegateable``
    """
    if allow_creator and delegateable and c.user and c.user == delegateable.creator:
        return True
    if c.user and (has_permission_bool('instance.admin') or has_permission_bool('global.admin')):
        return True
    if c.user and has_permission_bool(permission_name):
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
        redirect_to('/d/%d' % delegateable.id)
        
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


    