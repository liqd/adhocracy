from adhocracy.tests import *

class TestTwitteroauthController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='twitteroauth', action='index'))
        # Test response...
