
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

def motion_activity(motions):
    return sorted(motions, key=lambda m: estats.motion_activity(m))

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
                  key=lambda c: karma.comment_score(c, recurse=True),
                  reverse=True)

def comment_id(comments):
    return sorted(comments, key=lambda c: c.id)