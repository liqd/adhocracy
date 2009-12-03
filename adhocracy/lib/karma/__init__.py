from pylons import tmpl_context as c

from sqlalchemy.orm.exc import NoResultFound

from adhocracy import model
from ..cache import memoize

import threshold
from scores import *

@memoize('user_comment_position')
def position(comment, user):
    q = model.meta.Session.query(model.Karma.value)
    q = q.filter(model.Karma.comment==comment)
    q = q.filter(model.Karma.donor==user)
    try:
        return q.one()[0]
    except NoResultFound:
        return None
    except:
        return q.all()[0][0]
