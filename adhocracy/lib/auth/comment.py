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
    if has('instance.admin'):
        return True
    return create()

    
def reply(parent):
    return create_on(parent.topic) and not parent.is_deleted()


def is_own(co):
    return c.user and co.creator == c.user

def is_special(co):
    return co.canonical or co == co.topic.comment

def edit(c):
    if has('instance.admin'):
        return True
    if not (has('comment.edit') and show(c)):
        return False
    if not c.topic.is_mutable() and is_special(c):
        return False
    if not is_special(c) and ((not c.wiki) and (not is_own(c))):
        return False
    return True

        
revert = edit

    
def delete(co):
    if co.topic.comment == co:
        return False
    if has('instance.admin'):
        return True
    if is_own(co) and (not co.is_edited()) and revert(co):
        return True
    return has('comment.delete') and show(co) and not \
        (not co.topic.is_mutable() and co.canonical)

    
def rate(c):
    return show(c) and has('vote.cast') \
            and c.poll is not None \
            and not c.poll.has_ended()

