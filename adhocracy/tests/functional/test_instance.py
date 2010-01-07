from adhocracy.tests import *
from adhocracy.tests.testtools import *
from nose.tools import *

class TestInstanceController(WebTestController):
    
    def _is_member(self):
        res = self.app.get('/user/%s' % self.user.user_name)
        return not "not a member of" in res
            
    def test_nonmember_can_join_instance(self):
        pass
        #self.prepare_app()
        #assert_false(self._is_member())
        #self.app.get('/instance/join/test')
        #assert_true(self._is_member())
        
    def test_voter_can_leave_instance(self):
        pass
        #self.prepare_app(group_code=self.VOTER)
        #assert_true(self._is_member())
        #self.app.get('/instance/leave/test')
        #assert_false(self._is_member())