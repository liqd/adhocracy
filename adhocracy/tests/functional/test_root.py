from adhocracy.tests import TestController


class TestRootController(TestController):

    def test_root(self):
        response = self.app.get('/')
        self.assertEqual(response.status, '200 OK')

    def test_root_has_timeline(self):
        response = self.app.get('/')
        self.assertEqual(response.status, '200 OK')
        self.assertTrue('simile-ajax-api.js' in response.body)

    def test_root_has_login_link(self):
        response = self.app.get('/')
        self.assertEqual(response.status, '200 OK')
        self.assertTrue('<a href="/login">' in response.body)
        self.assertTrue('<a href="/register">' in response.body)
