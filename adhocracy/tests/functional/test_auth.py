from adhocracy.tests import *

class TestAuthController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='auth', action='index'))
        # Test response...
