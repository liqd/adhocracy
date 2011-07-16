import math
import logging

log = logging.getLogger(__name__)

from pylons import tmpl_context as c


def _popular_agents(delegations, count=10):
    """
    For a given set of delegations, find at most 'count' agents that
    occur most in the set. Returns a list of tuples, (agent, occurence_count)
    """
    agents = [d.agent for d in delegations if not d.revoke_time]
    freq = {}
    for agent in agents:
        freq[agent] = freq.get(agent, 0) + 1
    popular = sorted(freq.items(), cmp=lambda a, b: b[1] - a[1])
    popular = filter(lambda (u, v): u != c.user, popular)
    return popular[0:count]


def delegateable_popular_agents(delegateable, count=10):
    return _popular_agents(delegateable.delegations, count=count)


def user_popular_agents(user, count=10):
    return _popular_agents(user.delegated, count=count)


def log_with_null(n):
    return math.log(max(1, n))


def recommend(scope, user, count=5):
    dgb_pop_users = dict(delegateable_popular_agents(scope))
    usr_pop_users = dict(user_popular_agents(user))

    #log.debug("DGB POP DICT " + repr(dgb_pop_users))
    #log.debug("USR POP DICT " + repr(usr_pop_users))

    users = set(dgb_pop_users.keys() + usr_pop_users.keys())
    recs = dict()
    for u in users:
        if u == user or not u._has_permission('vote.cast'):
            continue
        recs[u] = (log_with_null(dgb_pop_users.get(u, 0)) * 2) + \
                  (usr_pop_users.get(u, 0) * 3)
    #log.debug("RECS DICT " + repr(recs))
    rs = sorted(recs.keys(), key=lambda u: recs[u], reverse=True)[0:count]
    #log.debug("RECS SORTING " + repr(rs))
    return rs
