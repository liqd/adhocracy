from adhocracy.tests import *

class TestWatchController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='watch', action='index'))
        # Test response...
