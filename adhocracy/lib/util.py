import uuid

def timedelta2seconds(delta):
    return delta.microseconds / 1000000.0 \
           + delta.seconds + delta.days * 60*60*24 
           
def random_token():
    return str(uuid.uuid4()).split('-').pop()