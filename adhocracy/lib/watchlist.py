
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

