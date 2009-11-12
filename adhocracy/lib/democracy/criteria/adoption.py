from criterion import Criterion

class AdoptionCriterion(Criterion):
    
    def check_tally(self, tally):
        return self.state.stable(tally) or \
               self.state.volatile(tally)


