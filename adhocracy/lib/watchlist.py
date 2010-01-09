import logging
from datetime import datetime

from sqlalchemy import or_
from sqlalchemy.orm import eagerload

from pylons import tmpl_context as c, request
import formencode

import adhocracy.model as model
import adhocracy.model.refs as refs

log = logging.getLogger(__name__)

def entity2ref(entity):
    return refs.to_ref(entity)

def watch_entity(user, entity):
    return watch_ref(user, entity2ref(entity))

def watch_ref(user, ref):
    # TODO: Subtransaction. 
    watch = model.Watch(user, refs.ref_type(ref), ref)
    model.meta.Session.add(watch)
    model.meta.Session.commit()
    return watch

def get_entity_watch(user, entity):
    return get_ref_watch(user, entity2ref(entity))

def get_ref_watch(user, ref):
    watch = model.Watch.find(user, ref)
    return watch

def get_entity_watches(entity):
    return get_ref_watches(entity2ref(entity))
    
def get_ref_watches(ref):
    q = model.meta.Session.query(model.Watch)
    q = q.filter(model.Watch.entity_ref==ref)
    q = q.filter(or_(model.Watch.delete_time==None,
                     model.Watch.delete_time>datetime.utcnow()))
    q = q.options(eagerload(model.Watch.user))
    return q.all()

def has_entity_watch(entity):
    return has_ref_watch(entity2ref(entity))

def has_ref_watch(ref):
    if not c.user:
        return None
    if not request.environ.get('adhocracy.user.watchlist'):
        q = model.meta.Session.query(model.Watch.entity_ref)
        q = q.filter(model.Watch.user==c.user)
        q = q.filter(or_(model.Watch.delete_time==None,
                         model.Watch.delete_time>datetime.utcnow()))
        request.environ['adhocracy.user.watchlist'] = \
            map(lambda x: x[0], q.all())
    return ref in request.environ.get('adhocracy.user.watchlist')

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
                watch_entity(c.user, entity)
        else:
            if watch:
                watch.delete()
                model.meta.Session.commit()        
    except formencode.Invalid:
        return None
    
def clean_stale_watches():
    log.debug("Beginning to clean up watchlist entries...")
    count = 0
    for watch in model.Watch.all():
        entity = refs.to_entity(watch.entity_ref)
        if hasattr(entity, 'is_deleted') and \
            entity.is_deleted():
            count += 1
            watch.delete()
    model.meta.Session.commit()
    if count > 0:
        log.debug("Removed %d stale watchlist entries." % count)    
            
