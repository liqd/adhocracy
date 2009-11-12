from criterion import Criterion

class AlternativesCriterion(Criterion):
    
    def get_alternatives(self, at_time):
        def valid(a):
            return a.create_time <= at_time and \
                    (not a.delete_time or a.delete_time > at_time)
        als = [a.other(self.motion) for a in self.motion.right_alternatives if valid(a)]
        als += [a.other(self.motion) for a in self.motion.left_alternatives if valid(a)]
        return set(als)     
    
    alternatives = property(lambda self: self.get_alternatives(self.state.at_time))   
    
    def check_blocking(self, at_time, path):
        if not (self.state.majority and self.state.participation):
            return False
        if self.check_blocked(at_time, path=path):
            return False
        return True      
    
    def alternative_blocks(self, alternative, at_time, path=[]):
        alt_state = type(self.state)(alternative) # ugly, better?
        return alt_state.alternatives.check_blocking(at_time, path=path)
    
    blocking = lambda self, alternative: self.alternative_blocks(alternative, 
                                                                 self.state.at_time)
    
    def check_blocked(self, at_time, path=None):
        if not path:
            path = [self]
        elif self in path:
            return False
        else: 
            path.append(self)
        
        for alternative in self.get_alternatives(at_time):
            if self.alternative_blocks(alternative, at_time, path=path):
                return True
        return False
    
    def check_tally(self, tally):
        return not self.check_blocked(tally.at_time)
