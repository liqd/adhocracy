from adhocracy.tests import WebTestController


class TestInstanceController(WebTestController):

    def _is_member(self):
        res = self.app.get('/user/%s' % self.user.user_name)
        return not "not a member of" in res

    def test_nonmember_can_join_instance(self):
        pass
        #self.prepare_app()
        #self.assertFalse(self._is_member())
        #self.app.get('/instance/join/test')
        #self.assertTrue(self._is_member())

    def test_voter_can_leave_instance(self):
        pass
        #self.prepare_app(group_code=self.VOTER)
        #self.assertTrue(self._is_member())
        #self.app.get('/instance/leave/test')
        #self.assertFalse(self._is_member())
