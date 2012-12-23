# -*- coding: utf-8 -*-

from datetime import datetime
import math
import re
import unicodedata

from adhocracy.lib.event import stats as estats
from adhocracy.lib.util import timedelta2seconds, datetime2seconds


PREFIXES = ['die', 'der', 'das', 'the', 'a', 'le', 'la']


def _not_combining(char):
        return unicodedata.category(char) != 'Mn'


def _strip_accents(text):
        unicode_text = unicodedata.normalize('NFD', text)
        return filter(_not_combining, unicode_text)


def _human_key(key):
    parts = re.split('([\d\.]+|.*)', key, maxsplit=1)
    keys = []
    if len(parts) > 1:
        keys.append([int(e) if e.isdigit() else e.swapcase()
                     for e in re.split('(\d+|\.)', parts[1])])
    if len(parts) > 2:
        keys.append(parts[2])

    keys = filter(lambda s: s not in PREFIXES, keys)
    keys = map(lambda s: isinstance(s, unicode) and
               _strip_accents(s) or s, keys)

    return keys


def sortable_text(value_list, key=None):
    """ String sorting by more human rules. """
    results = list(value_list)
    results.sort(key=lambda i: _human_key(key(i)))

    return results


def delegateable_label(entities):
    return sortable_text(entities, key=lambda e: e.label)


def instance_label(entities):
    return sortable_text(entities, key=lambda e: e.label)


def delegateable_title(entities):
    return sortable_text(entities, key=lambda e: e.title)


def hierarchical_title(entities):
        return delegateable_title(entities)


def delegateable_full_title(entities):
    return sortable_text(entities, key=lambda e: e.full_title)


def delegateable_latest_comment(entities):
    return sorted(entities, key=lambda e: e.find_latest_comment_time(),
                  reverse=True)


def score_and_freshness_sorter(max_age):
    '''
    Factory. Returns a function that calculates a sortable 60 character
    string from a combination of *max_age* and the parameters of the
    returned function, *score* and *time*.

    Factory:

    *max_age*
       Maximal age in seconds (*int*). This configures the returned
       function to increase the returned value if the passed *time*
       is less than *max_age* seconds in the past (compared to now).

    Returns: A function

    Returned function:

    *score*
       *int* or *float*. An int or float used to increase the value of the
       returned string.
    *time*
       A :class:`datetime.datetime` object. Usually the creation date
       of the object we calculate the string for

    Returns: A 60 character string.
    '''
    def _with_age(score, time):
        freshness = 1
        if score > -1:
            age = timedelta2seconds(datetime.utcnow() - time)
            freshness = math.log10(max(10, max_age - age))
        str_time = "%020d" % datetime2seconds(time)
        str_score_freshness = "%029.10f" % (freshness * score)
        return str_score_freshness + str_time
    return _with_age


def proposal_mixed_key(proposal):
    max_age = 172800  # 2 days
    scorer = score_and_freshness_sorter(max_age)
    tally = proposal.rate_poll.tally
    return scorer(tally.num_for - tally.num_against, proposal.create_time)


def proposal_mixed(entities):
    return sorted(entities, key=proposal_mixed_key, reverse=True)


def proposal_support(entities):
    return sorted(entities,
                  key=lambda p: p.rate_poll.tally.num_for, reverse=True)


def norm_selections(entities):
    return sorted(entities, key=lambda n: len(n.selections), reverse=True)


def norm_variants(entities):
    return sorted(entities, key=lambda n: len(n.variants), reverse=True)


def comment_order_key(comment):
    max_age = 43200  # 0.5 days
    scorer = score_and_freshness_sorter(max_age)
    return scorer(comment.poll.tally.score, comment.create_time)


def comment_order(comments):
    return sorted(comments, key=comment_order_key, reverse=True)


def user_name(entities):
    return sorted(entities, key=lambda e: e.name.lower())


def milestone_time(entities):
    return sorted(entities, key=lambda e: e.time)


def polls_time(entities):
    return sorted(entities, key=lambda e: e.end_time)


def entity_newest(entities):
    return sorted(entities, key=lambda e: e.create_time, reverse=True)


def entity_oldest(entities):
    return sorted(entities, key=lambda e: e.create_time, reverse=False)


def entity_stable(entities):
    return entities


def instance_activity(instances):
    return sorted(instances, key=lambda i: estats.instance_activity(i),
                  reverse=True)


def user_activity(instance, users):
    return sorted(users, key=lambda u: estats.user_activity(instance, u),
                  reverse=True)


def user_activity_factory(instance):
    '''
    Create an user activity sorting function that uses
    the given *instance*. If *instance* is `None`, the returned
    function will sort users by the activity across all instances.
    If instance is an :class:`adhocracy.model.Instance` object,
    it will sort the users by their activity in the given instance.

    Returns: A function that accepts a list of users and returns
    them sorted.
    '''
    def func(users):
        return user_activity(instance, users)
    return func


def comment_score(comments):
    return sorted(comments, key=lambda c: c.poll.tally.score,
                  reverse=True)


def dict_value_sorter(dict):
    def _sort(items):
        return sorted(items, key=lambda i: dict.get(i))
    return _sort


def comment_id(comments):
    return sorted(comments, key=lambda c: c.id)
