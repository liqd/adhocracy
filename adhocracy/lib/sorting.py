
import event.stats as estats
import karma

def delegateable_label(entities):
    return sorted(entities, key=lambda e: e.label.lower())

def user_name(entities):
    return sorted(entities, key=lambda e: e.name.lower())

def entity_newest(entities):
    return sorted(entities, key=lambda e: e.create_time, reverse=True)

def entity_oldest(entities):
    return sorted(entities, key=lambda e: e.create_time, reverse=False)

def issue_activity(issues):
    return sorted(issues, key=lambda i: estats.issue_activity(i))

def proposal_activity(proposals):
    return sorted(proposals, key=lambda m: estats.proposal_activity(m))

def instance_activity(instances):
    return sorted(instances, key=lambda i: estats.instance_activity(i))

def user_activity(users):
    return sorted(users, key=lambda u: estats.instance_activity(u))

def user_karma(users):
    return sorted(users, key=lambda u: karma.user_score(u), reverse=True)

def dict_value_sorter(dict):
    def _sort(items):
        return sorted(items, key=lambda i: dict.get(i))
    return _sort

def comment_karma(comments):
    return sorted(comments, 
                  key=lambda c: karma.comment_score(c),
                  reverse=True)

def comment_id(comments):
    return sorted(comments, key=lambda c: c.id)


#
# Unadapted Ruby, either find a python lib with p distribution tables or 
# hardcode the "power" argument. 
#
#def wilson_confidence_interval(pos, n, power):
#    if n == 0:
#        return 0
#    
#    z = Statistics2.pnormaldist(1-power/2)
#    phat = 1.0*pos/n
#    (phat + z*z/(2*n) - z * Math.sqrt((phat*(1-phat)+z*z/(4*n))/n))/(1+z*z/n)