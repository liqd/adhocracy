from datetime import datetime


class SimpleTally(object):
    """ A tally class without any backend to get data from. """
    def __init__(self, poll, num_for, num_against, num_abstain):
        self.poll = poll
        self.num_for = num_for
        self.num_against = num_against
        self.num_abstain = num_abstain


def make_from_poll(tally_cls, poll, at_time=None, user_filter=None):
    from adhocracy.lib.democracy import Decision
    from adhocracy.model import Vote
    if at_time is None:
        at_time = datetime.utcnow()
    results = {}
    decisions = Decision.for_poll(poll, at_time=at_time,
                                  user_filter=user_filter)
    for decision in decisions:
        if not decision.is_decided():
            continue
        results[decision.result] = results.get(decision.result, 0) + 1
    tally = tally_cls(poll,
                      results.get(Vote.YES, 0),
                      results.get(Vote.NO, 0),
                      results.get(Vote.ABSTAIN, 0))
    tally.create_time = at_time
    return tally
