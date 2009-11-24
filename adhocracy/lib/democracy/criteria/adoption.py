from ...cache import memoize

from criterion import Criterion

class AdoptionCriterion(Criterion):
    
    @memoize('adoption_tally')
    def check_tally(self, tally):
        return self.state.stable(tally) or \
               self.state.volatile(tally)
               
    def __str__(self):
        return "<AdoptionCriterion(%s)>" % (self.state.poll.id if self.state.poll else None)


