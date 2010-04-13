import adhocracy.model as model 
from pylons import tmpl_context as c
from authorization import has_permission_bool as has


def index():
    return has('comment.view')
    
def show(c):
    return has('comment.view') and not c.is_deleted()

def create():
    return has('comment.create')
    
def create_on(topic, canonical=False):
    if canonical and not isinstance(topic, model.Proposal):
        return False
    if canonical and not topic.is_mutable():
        return False
    return create()
    
def reply(parent):
    return create_on(parent.topic) and not parent.is_deleted()
    
def edit(c):
    return has('comment.edit') and show(c) and not \
        (not c.topic.is_mutable() and c.canonical)
        
revert = edit
    
def delete(co):
    if c.user and co.creator == c.user and \
        (not co.is_edited()) and revert(co):
        return True
    return has('comment.delete') and show(co) and not \
        (not co.topic.is_mutable() and co.canonical)
    
def rate(c):
    return show(c) and has('vote.cast') \
            and c.poll is not None \
            and not c.poll.has_ended()