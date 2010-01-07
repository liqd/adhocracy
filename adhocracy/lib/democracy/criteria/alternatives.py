from criterion import RelationCriterion, RelationLoop

class AlternativesCriterion(RelationCriterion):
    
    def get_alternatives(self, at_time):
        def valid(a):
            return a.create_time <= at_time and \
                    (not a.delete_time or a.delete_time > at_time)
        als = [a.other(self.proposal) for a in self.proposal.right_alternatives if valid(a)]
        als += [a.other(self.proposal) for a in self.proposal.left_alternatives if valid(a)]
        return set(als)     
    
    alternatives = property(lambda self: self.get_alternatives(self.state.at_time))   
    
    def alternative_blocks(self, alternative, at_time):
        state = self.create_state(alternative, at_time)
        return state.adopted
    
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

    def check_nopoll(self):
        return not self.check_blocked(self.state.at_time)
    
    def __str__(self):
        return "<AlternativesCriterion(%s)>" % (self.state.poll.id if self.state.poll else None)