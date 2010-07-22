from pylons import tmpl_context as c
from authorization import has
import poll

def index():
    return has('watch.show')
    
def show(w):
    return has('watch.show') and not w.is_deleted()

def create():
    return has('watch.create')
    
def delete(w):
    return has('watch.delete') and show(w)
    