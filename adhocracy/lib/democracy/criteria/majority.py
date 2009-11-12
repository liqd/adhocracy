from criterion import Criterion

class MajorityCriterion(Criterion):
    """
    Check to see whether the majority of those voting either to 
    affirm or dissent chose to affirm the poll. 
    """
    
    def _get_required(self):
        return self.motion.instance.required_majority
    
    required = property(_get_required)
    
    def check_tally(self, tally):
        return tally.rel_for > self.required 