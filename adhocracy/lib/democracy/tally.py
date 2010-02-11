import adhocracy.model as model
from adhocracy.model import Vote
from decision import Decision

from pylons import g


def _tally_key(poll, time):
    """ Unique ID for memcached. """
    return "tally_" + str(poll.id + hash(time.ctime()) * 13)

def at(poll, at_time):
    """ Generate a tally on poll at the given time. """
    tally = model.Tally.find_by_poll_and_time(poll, at_time)
    if tally is None:
        tally = model.Tally.create_from_poll(poll, at_time)
    return tally

def interval(poll, min_time=None, max_time=None):
    """ Generate a list of tallies for the specified interval. """
    return model.Tally.poll_by_interval(poll, min_time, max_time)

