# -*- coding: utf-8 -*-

from datetime import datetime
import math
from operator import attrgetter
import re
import unicodedata

from adhocracy.lib.util import timedelta2seconds, datetime2seconds


PREFIXES = ['die', 'der', 'das', 'the', 'a', 'le', 'la']


def _not_combining(char):
        return unicodedata.category(char) != 'Mn'


def _strip_accents(text):
    unicode_text = unicodedata.normalize('NFD', text)
    return filter(_not_combining, unicode_text)


def _human_key(key):
    keys = re.split('(\d+)', key)
    keys = map(lambda s: int(s) if s.isdigit() else s.lower(), keys)
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


def score_and_freshness_sorter(max_age=0):
    '''
    Factory. Returns a function that calculates a sortable 60 character
    string from a combination of *max_age* and the parameters of the
    returned function, *score* and *time*.

    Factory:

    *max_age*
       Maximal age in seconds (*int*). This configures the returned
       function to increase the returned value if the passed *time*
       is less than *max_age* seconds in the past (compared to now).

       If max_age is 0 (default) the freshness isn't taken into account.

    Returns: A function

    Returned function:

    *score*
       *int* or *float*. An int or float used to increase the value of the
       returned string.
    *time*
       A :class:`datetime.datetime` object. Usually the creation date
       of the object we calculate the string for
    *impact*
       An *int* between -10 and +10, which is used as primary sort key.

    Returns: A 60 character string.
    '''
    def _with_age(score, time, impact=0):

        if score > -1:
            age = timedelta2seconds(datetime.utcnow() - time)
            # freshness = 1 .. 5.2 if max_age == 2 days
            freshness = math.log10(max(10, max_age - age))
        else:
            freshness = 1

        # atan normalizes to -pi/2 .. +pi/2
        base = math.atan(freshness * score)

        # add impact
        assert -10 <= impact <= 10
        result = base + impact * math.pi

        str_time = "%020d" % datetime2seconds(time)
        str_score_freshness = "%029.10f" % (result)

        return str_score_freshness + str_time
    return _with_age


def proposal_mixed_key(proposal):
    max_age = 172800  # 2 days
    scorer = score_and_freshness_sorter(max_age)
    tally = proposal.rate_poll.tally

    # the badge with the highest absolute impact value wins
    impact = reduce(lambda a, b: b if abs(b) > abs(a) else a,
                    map(lambda d: d.badge.impact, proposal.delegateablebadges),
                    0)

    return scorer(tally.num_for - tally.num_against, proposal.create_time,
                  impact)


def proposal_mixed(entities):
    return sorted(entities,
                  key=lambda x: float(proposal_mixed_key(x)),
                  reverse=True)


def proposal_support_impact_key(proposal):
    scorer = score_and_freshness_sorter()
    score = proposal.rate_poll.tally.score

    # the badge with the highest absolute impact value wins
    impact = reduce(lambda a, b: b if abs(b) > abs(a) else a,
                    map(lambda d: d.badge.impact, proposal.delegateablebadges),
                    0)

    return scorer(score, proposal.create_time, impact)


def proposal_support_impact(entities):
    return sorted(entities,
                  key=lambda x: float(proposal_support_impact_key(x)),
                  reverse=True)


def proposal_controversy_calculate(num_for, num_against):
    '''
    Measure how disputed an issue is - 50 pro 50 contra should be way more
    important than an issue that ranks 99 pro 1 contra.

    Intuitively, min(pro, contra) / (pro + contra) should give the percentage
    of voters that disagree with the majority, and therefore be a good
    measurement.

    At the same time, we want issues with more absolute votes to rank slightly
    higher; 40 - 60 is way more important than 10 - 10. Therefore, we scale
    the whole sorting key by the logarithm of the total number of votes.

    See http://goo.gl/yZj2H for a plot of the function.
    '''

    if num_for + num_against == 0:
        return -1

    return (float(min(num_for, num_against))
            / (num_for + num_against)
            * math.log(num_for + num_against))


def proposal_controversy_key(proposal):
    tally = proposal.rate_poll.tally
    return proposal_controversy_calculate(tally.num_for, tally.num_against)


def proposal_controversy(entities):
    return sorted(entities, key=proposal_controversy_key, reverse=True)


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
    return sorted(entities, key=attrgetter('time', 'title'))


def polls_time(entities):
    return sorted(entities, key=lambda e: e.end_time)


def entity_newest(entities):
    return sorted(entities, key=lambda e: e.create_time, reverse=True)


def entity_oldest(entities):
    return sorted(entities, key=lambda e: e.create_time, reverse=False)


def entity_stable(entities):
    return entities


def instance_activity(instances):
    from adhocracy.lib.event import stats as estats
    return sorted(instances, key=lambda i: estats.instance_activity(i),
                  reverse=True)


def user_activity(instance, users):
    from adhocracy.lib.event import stats as estats
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
