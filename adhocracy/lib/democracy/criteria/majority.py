from criterion import Criterion

class MajorityCriterion(Criterion):
    """
    Check to see whether the majority of those voting either to 
    affirm or dissent chose to affirm the poll. 
    """
    
    def _get_required(self):
        return self.proposal.instance.required_majority
    
    required = property(_get_required)
    
    def check_tally(self, tally):
        return tally.rel_for > self.required 
    
    def __str__(self):
        return "<MajorityCriterion(%s)>" % (self.state.poll.id if self.state.poll else None)