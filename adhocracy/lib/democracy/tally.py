import adhocracy.model as model
from adhocracy.model import Vote
from decision import Decision

from pylons import g


def _tally_key(poll, time):
    """ Unique ID for memcached. """
    return "tally_" + str(poll.id + hash(time.ctime()) * 13)

def at(poll, at_time):
    """ Generate a tally on poll at the given time. """
    key = _tally_key(poll, at_time)
    #print "NEED TALLY"
    if g.cache:
        tally = g.cache.get(key)
        if tally:
            return tally
    tally = Tally.from_decisions(Decision.for_poll(poll, at_time=at_time), 
                                 at_time)
    #print "MADE TALLY"
    if g.cache:
        g.cache.set(key, tally)
    return tally

def interval(poll, min_time=None, max_time=None):
    """ Generate a list of tallies for the specified interval. """
    query = model.meta.Session.query(Vote.create_time)
    query = query.filter(Vote.poll_id==poll.id)
    if min_time:
        query = query.filter(Vote.create_time>=min_time)
    if max_time:
        query = query.filter(Vote.create_time<=max_time)
    tallies = []
    if not g.cache:
        tallies = [at(poll, t) for t in times]
    else:
        times = dict([(t[0], _tally_key(poll, t[0])) for t in query])
        cached = g.cache.get_multi(times.values())
        for time in times.keys():
            tally = cached.get(times[time], None)
            if not tally:
                tally = at(poll, time)
            tallies.append(tally)
    return sorted(tallies, key=lambda t: t.at_time, reverse=True)


class Tally(object):
    
    def __init__(self, positions, at_time):
        self.at_time = at_time
        self.positions = positions
   
    def _filter_positions(self, position):
        return filter(lambda p: p == position, self.positions)
    
    def _get_num_affirm(self):
        """ Number of voters who affirmed the motion. """
        return len(self._filter_positions(Vote.AYE))
    
    num_affirm = property(_get_num_affirm) 
    
    def _get_num_dissent(self):
        """ Number of voters who dissent on the motion. """
        return len(self._filter_positions(Vote.NAY))
    
    num_dissent = property(_get_num_dissent) 
    
    def _get_num_abstain(self):
        """ Number of voters who abstained from the motion. """
        return len(self._filter_positions(Vote.ABSTAIN))
    
    num_abstain = property(_get_num_abstain) 
    
    def _get_rel_for(self):
        """ Fraction of decided voters who are for the motion. """
        if self.num_affirm == 0 and self.num_dissent == 0:
            return 0.5
        return self.num_affirm / float(max(1, self.num_affirm + self.num_dissent))
                                                    
    rel_for = property(_get_rel_for)
        
    def _get_rel_against(self):
        """ Fraction of decided voters who are against the motion. """
        return 1 - self.rel_for
                                                    
    rel_against = property(_get_rel_against)
    
    def __len__(self):
        return len(self.positions)
    
    def __repr__(self):
        return "<Tally(%s,%s{+%s:-%s:*%s},%s%% v. %s%%)>" % (
                      self.at_time if self.at_time else "now",
                      len(self), self.num_affirm,
                      self.num_dissent, self.num_abstain, 
                      int(self.rel_for * 100), int(self.rel_against * 100))
    
    @classmethod
    def from_decisions(cls, decisions, at_time):
        decisions = filter(lambda d: d.made(), decisions)
        return cls(map(lambda d: d.result, decisions), at_time)
    