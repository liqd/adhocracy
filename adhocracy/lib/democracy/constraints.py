from datetime import datetime

import adhocracy.model as model
from poll import Poll, NoPollException

class DependencyConstraint(object):
    
    def __init__(self, motion, result_class, at_time=None):
        if not at_time:
            at_time = datetime.now()
        self.at_time = at_time
        self.motion = motion
        self.result_class = result_class
        
    def _met(self):
        for dependency in self.motion.dependencies:
            try:
                poll = Poll(dependency.requirement, at_time=self.at_time)
                result = self.result_class(poll)
                print "DEP ", dependency, " RES ", result.state
                if not result.state in model.Motion.FULFILLING_STATES:
                    return False
            except NoPollException:
                return False
        return True
    
    met = property(_met)
    
class AntinomyConstraint(object):
    
    def __init__(self, motion, result_class, at_time=None):
        pass
    
    def _met(self):
        return True
    
    met = property(_met) 