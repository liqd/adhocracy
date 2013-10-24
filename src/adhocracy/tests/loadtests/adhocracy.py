import unittest
from funkload.FunkLoadTestCase import FunkLoadTestCase


class Adhocracy(FunkLoadTestCase):
    """This test uses the configuration file ADHOCRACY.conf."""

    def setUp(self):
        self.server_url = self.conf_get('main', 'url')

    def test_instance_startpage(self):
        # The description should be set in the configuration file
        server_url = self.server_url
        # begin of test ---------------------------------------------
        self.get(server_url, description='Get startpage url')
        self.get(server_url + "/instance", description='Go to instances')
        self.get(server_url + "/i/test/instance/test",
                 description='Go to test instance')
        # end of test -----------------------------------------------

if __name__ in ('main', '__main__'):
    unittest.main()
