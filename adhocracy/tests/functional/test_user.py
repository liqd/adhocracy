from adhocracy.tests import *

class TestUserController(WebTestController):
    
    def test_skip_authentication_login(self):
        pass
        #self.set_user(self.VOTER)
        #resp = self.app.get('/') # '/user/edit/%s' % self.user.user_name) #, extra_environ=environ)
        #assert resp.code == 200
        