from pylons import tmpl_context as c

from adhocracy import model
from ..cache import memoize

import math

@memoize('comment_score')
def comment_score(comment, recurse=False):
    score = 1 
    if recurse:
        score += sum(map(lambda c: comment_score(c, recurse=True), comment.replies))
    q = model.meta.Session.query(model.Karma)
    q = q.filter(model.Karma.comment==comment)
    try:
        karmas = q.all()
        return score + sum([k.value for k in karmas])
    except:
        return score

def user_score(user):
    @memoize('user_instance_score')
    def _user_score(user, instance):
        q = model.meta.Session.query(model.Karma)
        q = q.filter(model.Karma.recipient==user)
        q = q.filter(model.Karma.donor!=user)
        karmas = q.all()
        if instance:
            karmas = [k for k in karmas if k.comment.topic.instance == c.instance]
        score = 1 + sum([k.value for k in karmas])
        return max(0, score)
    return _user_score(user, c.instance)


#
# Unadapted Ruby, either find a python lib with p distribution tables or 
# hardcode the "power" argument. 
#
def wilson_confidence_interval(pos, n, power):
    if n == 0:
        return 0
    
    z = Statistics2.pnormaldist(1-power/2)
    phat = 1.0*pos/n
    (phat + z*z/(2*n) - z * Math.sqrt((phat*(1-phat)+z*z/(4*n))/n))/(1+z*z/n)