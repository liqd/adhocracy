# -*- coding: utf-8 -*-

import math
import re
from datetime import datetime

from adhocracy.lib.event import stats as estats
from adhocracy.lib.util import timedelta2seconds

SPLIT_RE = re.compile(r"[\s\.,;:]")
PREFIXES = ['die', 'der', 'das', 'the', 'a', 'le', 'la']


def sortable_text(text):
    """ String sorting by more human rules. """
    text = text.lower()
    text = text.replace(u'ä', 'a')
    text = text.replace(u'ü', 'u')
    text = text.replace(u'ö', 'o')
    text = text.replace(u'é', 'e').replace(u'è', 'e')
    text = text.replace(u'á', 'a').replace(u'à', 'a')
    parts = []
    for part in SPLIT_RE.split(text):
        # will enter this to IOCCC soon.
        if part in PREFIXES:
            continue
        try:
            parts.append(int(part) * 1000000)
        except ValueError:
            parts.extend(map(ord, part))
    return parts


def delegateable_label(entities):
    return sorted(entities, key=lambda e: sortable_text(e.label))


def instance_label(entities):
    return sorted(entities, key=lambda e: sortable_text(e.label))


def delegateable_title(entities):
    return sorted(entities, key=lambda e: sortable_text(e.title))


def delegateable_full_title(entities):
    return sorted(entities, key=lambda e: sortable_text(e.full_title))


def delegateable_latest_comment(entities):
    return sorted(entities, key=lambda e: e.find_latest_comment_time(),
                  reverse=True)


def score_and_freshness_sorter(max_age):
    def _with_age(score, time):
        freshness = 1
        if score > -1:
            age = timedelta2seconds(datetime.utcnow() - time)
            freshness = max(1, math.log10(max(1, max_age - age)))
        return (freshness * score, time)
    return _with_age


def proposal_mixed(entities):

    def _proposal_key(proposal):
        max_age = 3600 * 36  # 2 days
        scorer = score_and_freshness_sorter(max_age)
        return scorer(proposal.rate_poll.tally.num_for, proposal.create_time)

    return sorted(entities, key=_proposal_key, reverse=True)


def proposal_support(entities):
    return sorted(entities,
                  key=lambda p: p.rate_poll.tally.num_for, reverse=True)


def norm_selections(entities):
    return sorted(entities, key=lambda n: len(n.selections), reverse=True)


def norm_variants(entities):
    return sorted(entities, key=lambda n: len(n.variants), reverse=True)


def comment_order(comments):
    def _comment_key(comment):
        max_age = 84600 / 2  # 0.5 days
        scorer = score_and_freshness_sorter(max_age)
        return scorer(comment.poll.tally.score, comment.create_time)
    return sorted(comments, key=_comment_key, reverse=True)


def user_name(entities):
    return sorted(entities, key=lambda e: e.name.lower())


def milestone_time(entities):
    return sorted(entities, key=lambda e: e.time)


def entity_newest(entities):
    return sorted(entities, key=lambda e: e.create_time, reverse=True)


def entity_oldest(entities):
    return sorted(entities, key=lambda e: e.create_time, reverse=False)


def entity_stable(entities):
    return entities


def instance_activity(instances):
    return sorted(instances, key=lambda i: estats.instance_activity(i),
                  reverse=True)


def user_activity(users):
    return sorted(users, key=lambda u: estats.instance_activity(u),
                  reverse=True)


def comment_score(comments):
    return sorted(comments, key=lambda c: c.poll.tally.score,
                  reverse=True)


def dict_value_sorter(dict):
    def _sort(items):
        return sorted(items, key=lambda i: dict.get(i))
    return _sort


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


