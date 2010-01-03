import uuid
from pylons.controllers.util import abort


def timedelta2seconds(delta):
    """ Convert a given timedelta to a number of seconds """
    return delta.microseconds / 1000000.0 \
           + delta.seconds + delta.days * 60*60*24 
           
def random_token():
    """ Get a random string, the first char group of a uuid4 """
    return str(uuid.uuid4()).split('-').pop()

def get_entity_or_abort(cls, id, instance_filter=True):
    """ 
    Return either the instance identified by the given ID or
    raise a HTTP 404 Exception within the controller. 
    """ 
    if not hasattr(cls, 'find'):
        raise TypeError("The given class does not have a find() method")
    obj = cls.find(id, instance_filter=instance_filter)
    if not obj:
        abort(404, "Could not find the entity '%s'" % id)
    return obj