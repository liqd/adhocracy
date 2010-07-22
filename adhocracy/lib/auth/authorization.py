import logging

from pylons import config, tmpl_context as c
from pylons import request
from pylons.controllers.util import abort
from pylons.i18n import _

from sqlalchemy import and_, or_
from sqlalchemy.orm import eagerload

from repoze.what.predicates import has_permission as what_has_permission
from repoze.what.adapters import BaseSourceAdapter, SourceError
from repoze.what.plugins.sql.adapters import SqlGroupsAdapter

import adhocracy.model as model 


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
        sections.append(u"Anonymous")
        return set(sections)
    
    
    def _get_item_as_row(self, item_name):
        q = model.meta.Session.query(model.User)
        q = q.filter(model.User.user_name==unicode(item_name))
        q = q.options(eagerload(model.User.memberships))
        try:
            return q.limit(1).first()
        except Exception, e:
            log.exception(e)
            raise SourceError("No such user: %s" % item_name)


class has_permission(what_has_permission):
    """
    This modified version of ``repoze.what``'s ``has_permission`` will apply ``Anonymous`` 
    rights to any user making requests. This allows to call ``has_permission`` on methods
    even when they are not protected, thus making the authorization system more 
    configurable.
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
        

def has(permission):
    return permission in request.environ.get('repoze.what.credentials', {}).get('permissions', [])
    #p = has_permission(permission)
    #return p.is_met(request.environ)


    