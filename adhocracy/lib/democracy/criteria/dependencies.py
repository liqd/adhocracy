from criterion import RelationCriterion, RelationLoop
    
class DependenciesCriterion(RelationCriterion):
    
    def get_dependencies(self, at_time):
        return [d.requirement for d in self.motion.dependencies if \
                    d.create_time <= at_time and \
                    (not d.delete_time or d.delete_time > at_time)]
    
    dependencies = property(lambda self: self.get_dependencies(self.state.at_time))
    
    def check_blocking(self, at_time):
        if not (self.state.majority and self.state.participation):
            return False
        if self.check_blocked(at_time):
            return False
        return True  
    
    def dependency_blocks(self, dependency, at_time):
        state = self.create_state(dependency, at_time)
        return state.dependencies.check_blocking(at_time)
    
    blocking = lambda self, dependency: self.dependency_blocks(dependency,
                                                              self.state.at_time)
    
    def check_blocked(self, at_time):
        try:
            self.loop_abort()
        except RelationLoop:
            return False
        
        for dependency in self.get_dependencies(at_time):
            if self.dependency_blocks(dependency, at_time):
                return True
        return False    
    
    def check_tally(self, tally):
        return not self.check_blocked(tally.at_time)