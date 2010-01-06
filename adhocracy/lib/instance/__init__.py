from decorator import decorator

from pylons import tmpl_context as c
from pylons.controllers.util import abort
from pylons.i18n import _

import adhocracy.model as model

from discriminator import setup_discriminator

def _RequireInstance(f, *a, **kw):
    if not c.instance:
        abort(404, _("This action is only available in an instance context."))
    else:
        return f(*a, **kw)
    
RequireInstance = decorator(_RequireInstance)

def create(key, label, user):
    #model.meta.Session.begin_nested()
    
    supervisor_grp = model.Group.by_code(model.Group.CODE_SUPERVISOR)
    instance = model.Instance(key, label, user)
    instance.default_group = model.Group.by_code(model.Group.INSTANCE_DEFAULT) 
    membership = model.Membership(user, instance, supervisor_grp, approved=True)
    model.meta.Session.add(instance)
    model.meta.Session.add(membership)
    model.meta.Session.commit()
    
    return instance
    