import math

from pylons import tmpl_context as c

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import eagerload

from adhocracy import model
from ..cache import memoize
from ..democracy import DelegationNode

@memoize('user_comment_position')
def position(comment, user):
    q = model.meta.Session.query(model.Karma.value)
    q = q.filter(model.Karma.comment==comment)
    q = q.filter(model.Karma.donor==user)
    try:
        return q.one()[0]
    except NoResultFound:
        return None

def comment_score(comment, recurse=False):
    score = 1 
    q = model.meta.Session.query(model.Karma)
    q = q.filter(model.Karma.comment==comment)
    q = q.options(eagerload(model.Karma.comment))
    q = q.options(eagerload(model.Karma.donor))
    for karma in q:
        dnode = DelegationNode(karma.donor, karma.comment.topic)
        # TODO: this is buggy in that it will lead to some votes
        # being cast twice. 
        score += karma.value * dnode.number_of_votes()
    return score

def delegateable_users(delegateable, donor=None):
    for comment in delegateable.comments:
        q = model.meta.Session.query(model.Karma)
        q = q.filter(model.Karma.comment==comment)
        if donor:
            q = q.filter(model.Karma.donor==donor)
        for k in q:
            val = user_scores.get(k.recipient, 0)
            user_scores[k.recipient] = val + k.value
    for child in delegateable.children: 
        scores = delegateable_users(child)
        for u, v in scores.items():
            val = user_scores.get(u, 0)
            user_scores[u] = val + v
    return user_scores

