# http://www.mail-archive.com/sqlalchemy@googlegroups.com/msg09203.html

from sqlalchemy.orm import MapperExtension, EXT_CONTINUE

PREINSERT = "_pre_insert"
PREDELETE = "_pre_delete"
PREUPDATE = "_pre_update"
POSTINSERT = "_post_insert"
POSTDELETE = "_post_delete"
POSTUPDATE = "_post_update"

class HookExtension(MapperExtension):
    """ Extention to add pre-commit hooks.

    Hooks will be called in Mapped classes if they define any of these
    methods:
      * _pre_insert()
      * _pre_delete()
      * _pre_update()
    """
    
    def before_insert(self, mapper, connection, instance):
        if getattr(instance, PREINSERT, None):
            instance._pre_insert()
        return EXT_CONTINUE

    def before_delete(self, mapper, connection, instance):
        if getattr(instance, PREDELETE, None):
            instance._pre_delete()
        return EXT_CONTINUE

    def before_update(self, mapper, connection, instance):
        if getattr(instance, PREUPDATE, None):
            instance._pre_update()
        return EXT_CONTINUE

    def after_insert(self, mapper, connection, instance):
        if getattr(instance, POSTINSERT, None):
            instance._post_insert()
        return EXT_CONTINUE

    def after_delete(self, mapper, connection, instance):
        if getattr(instance, POSTDELETE, None):
            instance._post_delete()
        return EXT_CONTINUE

    def after_update(self, mapper, connection, instance):
        if getattr(instance, POSTUPDATE, None):
            instance._post_update()
        return EXT_CONTINUE
    
def patch_some(clazz, hooks, f):
    for hook in hooks:
        patch(clazz, hook, f)
        
def patch_pre(clazz, f):
    patch_some(clazz, [PREINSERT, PREUPDATE, PREDELETE], f)
    
def patch_post(clazz, f):
    patch_some(clazz, [POSTINSERT, POSTUPDATE, POSTDELETE], f)
    
def patch_default(clazz, f):
    patch_some(clazz, [POSTINSERT, POSTUPDATE, PREDELETE], f)
        
def patch(clazz, hook, f):
    prev = getattr(clazz, hook, None)
    a = f
    if prev:
        def chain(*a, **kw):
            f(*a, **kw)
            prev(*a, **kw)
        a = chain
    setattr(clazz, hook, a)
        