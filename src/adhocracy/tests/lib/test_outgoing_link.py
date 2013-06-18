from adhocracy.tests import TestController

from adhocracy.lib.outgoing_link import rewrite_urls


class OutgoingLinkTest(TestController):
    def test_staticpage(self):
        from adhocracy.lib.staticpage import render_body
        r = render_body(u'<a href="http://example.com/">link</a>')
        self.assertTrue(u'href="http://example' not in r)

    def test_usercontent(self):
        from adhocracy.lib.text import render

        r = render(u'[link](http://example.com/)')
        self.assertTrue(u'href="http://example' not in r)

    def test_rewrite_urls(self):
        r = rewrite_urls(u'<a href="http://example.com/">link</a>')
        self.assertTrue(u'href="http://example' not in r)

        r = rewrite_urls(u'<a href="https://example.com/">link</a>')
        self.assertTrue(u'href="https://example' not in r)

        r = rewrite_urls(u'<a href="//example.com/">link</a>')
        self.assertTrue(u'href="//example' not in r)

        r = rewrite_urls(u'<a href="/">link</a>')
        self.assertTrue(u'href="/' in r)

        r = rewrite_urls(u'<a href="/i/foo/x/y">link</a>')
        self.assertTrue(u'href="/i/foo/x/y' in r)

        # Do not add any crap
        self.assertEqual(rewrite_urls(u''), u'')
        self.assertEqual(rewrite_urls(u'<a><img src="//example.com/i"/>x</a>'),
                         u'<a><img src="//example.com/i"/>x</a>')
