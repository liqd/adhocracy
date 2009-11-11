from adhocracy.tests import *

class TestPollController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='poll', action='index'))
        # Test response...
