from criterion import RelationCriterion, RelationLoop

class AlternativesCriterion(RelationCriterion):
    
    def get_alternatives(self, at_time):
        def valid(a):
            return a.create_time <= at_time and \
                    (not a.delete_time or a.delete_time > at_time)
        als = [a.other(self.motion) for a in self.motion.right_alternatives if valid(a)]
        als += [a.other(self.motion) for a in self.motion.left_alternatives if valid(a)]
        return set(als)     
    
    alternatives = property(lambda self: self.get_alternatives(self.state.at_time))   
    
    def check_blocking(self, at_time):
        if not (self.state.majority and self.state.participation):
            return False
        if self.check_blocked(at_time):
            return False
        return True      
    
    def alternative_blocks(self, alternative, at_time):
        state = self.create_state(alternative, at_time)
        return state.alternatives.check_blocking(at_time)
    
    blocking = lambda self, alternative: self.alternative_blocks(alternative, 
                                                                 self.state.at_time)
    
    def check_blocked(self, at_time):
        try:
            self.loop_abort()
        except RelationLoop:
            return False
        
        for alternative in self.get_alternatives(at_time):
            if self.alternative_blocks(alternative, at_time):
                return True
        return False
    
    def check_tally(self, tally):
        return not self.check_blocked(tally.at_time)

