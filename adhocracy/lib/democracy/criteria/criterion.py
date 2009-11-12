


class Criterion(object):
    
    def __init__(self, state):
        self.state = state
        self.motion = state.motion
        self.poll = state.poll
        self._checked = None
        
    def check(self):
        if self._checked == None:
            if self.state.polling:
                self._checked = self.check_tally(self.state.tally)
            else:
                self._checked = False
        return self._checked
    
    def check_tally(self, tally):
        raise NotImplemented()
    
    def __nonzero__(self):
        return self.check()
    
    def __call__(self, tally):
        return self.check_tally(tally)
    
    def __repr__(self):
        return "<Criterion(%s,%s)>" % (self.motion.id, self.poll.id)
    
    def __str__(self): 
        # relevant for cache keys
        return repr(self)
