import math

from social import * 
from karma import *

def log_with_null(n):
    return math.log(n) if n > 1 else 1

def recommend(scope, user, count=5):
    karma_users = delegateable_users(scope)
    donor_karma_users = delegateable_users(scope, donor=user)
    dgb_pop_users = dict(delegateable_popular_agents(scope))
    usr_pop_users = dict(user_popular_agents(user))
    
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
    return sorted(recs.keys(), key=lambda u: recs[u])[0:count]