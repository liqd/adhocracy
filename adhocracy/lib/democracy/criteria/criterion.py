from time import time
from ...cache import memoize

class Criterion(object):
    
    def __init__(self, state):
        self.state = state
        self.motion = state.motion
        self.poll = state.poll
        self._checked = None
    
    def check(self):
        if self._checked == None:
            #begin_time = time()
            @memoize('adoption_tally', 120)
            def _cached(self, poll, motion):
                if self.state.polling:
                    return self.check_tally(self.state.tally)
                else:
                    return self.check_nopoll()
            self._checked = _cached(self, self.state.poll, self.state.motion)
            #print "DEBUG TIME: ", str((time()-begin_time)*1000), "ms FOR ", type(self)
        return self._checked
    
    def check_tally(self, tally):
        raise NotImplemented()
    
    def check_nopoll(self):
        return False
    
    def __nonzero__(self):
        return self.check()
    
    def __call__(self, tally):
        return self.check_tally(tally)
    
    def __repr__(self):
        return "<Criterion(%s,%s)>" % (
                    self.motion.id if self.motion else None, 
                    self.poll.id if self.poll else None)
    
    def __str__(self): 
        # relevant for cache keys
        return repr(self)


class RelationLoop(Exception): pass

class RelationCriterion(Criterion):
    
    def _get_path(self):
        if not hasattr(self.state, 'relation_path'):
            return []
        return self.state.relation_path 
    
    def loop_abort(self):
        if self.motion in self._get_path():
            raise RelationLoop()
        
    def create_state(self, motion, at_time):
        state = type(self.state)(motion, at_time=at_time)
        state.relation_path = self._get_path() + [self.motion]
        return state
            