from adhocracy.tests import TestController

from adhocracy.lib.staticpage import render_body


class StaticPageTest(TestController):
    def test_render_body(self):
        r = render_body(u'<a href="http://example.com/">link</a>')
        self.assertTrue(u'href="http://example' not in r)

        r = render_body(u'<a href="https://example.com/">link</a>')
        self.assertTrue(u'href="https://example' not in r)

        r = render_body(u'<a href="//example.com/">link</a>')
        self.assertTrue(u'href="//example' not in r)

        r = render_body(u'<a href="/">link</a>')
        self.assertTrue(u'href="/' in r)

        r = render_body(u'<a href="/i/foo/x/y">link</a>')
        self.assertTrue(u'href="/i/foo/x/y' in r)

        # Do not add any crap
        self.assertEqual(render_body(u''), u'')
        self.assertEqual(render_body(u'<a><img src="//example.com/i"/>x</a>'),
                         u'<a><img src="//example.com/i"/>x</a>')
