from datetime import datetime

from pylons import tmpl_context as c, request
import formencode

import adhocracy.model as model
import search.entityrefs as entityrefs

def entity2ref(entity):
    return entityrefs.to_ref(entity)

def watch_entity(user, entity):
    return watch_ref(user, entity2ref(entity))

def watch_ref(user, ref):
    # TODO: Subtransaction. 
    watch = model.Watch(user, entityrefs.ref_type(ref), ref)
    model.meta.Session.add(watch)
    model.meta.Session.commit()
    return watch

def get_entity_watch(user, entity):
    return get_ref_watch(user, entity2ref(entity))

def get_ref_watch(user, ref):
    watch = model.Watch.find(user, ref)
    return watch

def check_watch(entity):
    if not c.user:
        return None
    try:
        watch_val = formencode.validators.Bool(not_empty=False,
                                               if_empty=False,
                                               if_missing=False)
        do_watch = watch_val.to_python(request.params.get('watch'))
        watch = get_entity_watch(c.user, entity)
        if do_watch: 
            if not watch:
                watch_entity(cuser, entity)
        else:
            if watch:
                watch.delete_time = datetime.now()
                model.meta.Session.add(watch)
                model.meta.Session.commit()        
    except formencode.Invalid:
        return None
