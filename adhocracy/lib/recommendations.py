import math
import sys

from social import * 
from karma import *

def log_with_null(n):
    return math.log(max(1,n))

def recommend(scope, user, count=5):
    karma_users = delegateable_users(scope)
    donor_karma_users = delegateable_users(scope, donor=user)
    dgb_pop_users = dict(delegateable_popular_agents(scope))
    usr_pop_users = dict(user_popular_agents(user))
    
    print >>sys.stderr, "KARMA DICT", repr(karma_users)
    print >>sys.stderr, "DONOR KARMA DICT", repr(donor_karma_users)
    print >>sys.stderr, "DGB POP DICT", repr(dgb_pop_users)
    print >>sys.stderr, "USR POP DICT", repr(usr_pop_users)
        
    users = set(karma_users.keys() + donor_karma_users.keys() + \
                dgb_pop_users.keys() + usr_pop_users.keys())
    recs = dict()
    for u in users:
        if u == user:
            continue
        recs[u] = (log_with_null(karma_users.get(u, 0)) * 1) + \
                  (donor_karma_users.get(u, 0) * 5) + \
                  (log_with_null(dgb_pop_users.get(u, 0)) * 2) + \
                  (usr_pop_users.get(u, 0) * 3)
    print >>sys.stderr, "RECS DICT", repr(recs)
    rs = sorted(recs.keys(), key=lambda u: recs[u], reverse=True)[0:count]
    print >>sys.stderr, "RECS SORTING", repr(rs)
    return rs