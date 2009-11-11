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