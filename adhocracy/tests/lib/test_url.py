import mock

from adhocracy.tests import TestController
from adhocracy.tests.testtools import tt_make_proposal


class TestUrls(TestController):

    def test_append_member_and_format_full(self):
        from adhocracy.lib.helpers.url import append_member_and_format
        appended = append_member_and_format(u'http://base-url/existing',
                                            member='new', format='html')
        self.assertEqual(appended, u'http://base-url/existing/new.html')

    def test_append_member_and_format_append_member(self):
        from adhocracy.lib.helpers.url import append_member_and_format
        appended = append_member_and_format(u'http://base-url/existing',
                                            member='new')
        self.assertEqual(appended, u'http://base-url/existing/new')

    def test_append_member_and_format_append_format(self):
        from adhocracy.lib.helpers.url import append_member_and_format
        appended = append_member_and_format(u'http://base-url/existing',
                                            format='html')
        self.assertEqual(appended, u'http://base-url/existing.html')

    def test_append_member_and_format_format_is_lowercased(self):
        from adhocracy.lib.helpers.url import append_member_and_format
        appended = append_member_and_format(u'http://base-url/existing',
                                            format='HTML')
        self.assertEqual(appended, u'http://base-url/existing.html')

    def test_build_global(self):
        from adhocracy.lib.helpers.url import build
        url = build(None, 'base', 'id', query={'param': 'arg'},
                    anchor='anchor', member='member', format="html")
        self.assertEqual(
            url, u'http://test.lan/base/id/member.html#anchor?param=arg')

    def test_build_global_omit_base(self):
        from adhocracy.lib.helpers.url import build
        url = build(None, None, 'id', query={'param': 'arg'},
                    anchor='anchor', member='member', format="html")
        self.assertEqual(url,
                         u'http://test.lan/id/member.html#anchor?param=arg')
        url = build(None, '', 'id', query={'param': 'arg'},
                    anchor='anchor', member='member', format="html")
        self.assertEqual(url,
                         u'http://test.lan/id/member.html#anchor?param=arg')

    def test_build_global_omit_member_and_format(self):
        from adhocracy.lib.helpers.url import build
        url = build(None, 'base', 'id', query={'param': 'arg'},
                    anchor='anchor')
        self.assertEqual(url, u'http://test.lan/base/id#anchor?param=arg')

    def test_build_global_omit_anchor_member_and_format(self):
        from adhocracy.lib.helpers.url import build
        url = build(None, 'base', 'id', query={'param': 'arg'},
                    anchor='anchor')
        self.assertEqual(url, u'http://test.lan/base/id#anchor?param=arg')

    def test_build_global_omit_query(self):
        from adhocracy.lib.helpers.url import build
        url = build(None, 'base', 'id', anchor='anchor', member='member',
                    format="html")
        self.assertEqual(url,
                         u'http://test.lan/base/id/member.html#anchor')

    def test_build_query_is_encoded(self):
        from adhocracy.lib.helpers.url import build
        url = build(None, 'base', 'id', query={'param': 'http://a@b:x'})
        self.assertEqual(
            url, u'http://test.lan/base/id?param=http%3A%2F%2Fa%40b%3Ax')

    def test_build_global_omit_all_except_id(self):
        from adhocracy.lib.helpers.url import build
        url = build(None, None, 'id')
        self.assertEqual(url, u'http://test.lan/id')

    def test_login_redirect(self):
        from adhocracy.lib.helpers import login_redirect_url

        proposal = tt_make_proposal(title='testproposal')
        url = login_redirect_url(proposal)
        expected = (u'http://test.test.lan/login?came_from='
                    u'http%3A%2F%2Ftest.test.lan%2Fproposal%2F2-testproposal')
        self.assertEqual(url, expected)


class TestInstanceUrls(TestController):

    mocked_path_func = mock.patch('adhocracy.lib.logo.path_and_mtime',
                                  return_value=('/dummy/path', 1234))

    def test_icon_url_with_y(self):
        with self.mocked_path_func:
            from adhocracy.lib import helpers as h
            from adhocracy.tests.testtools import tt_get_instance
            test_instance = tt_get_instance()
            url = h.instance.icon_url(test_instance, 48)
            self.assertEqual(
                url, 'http://test.test.lan/instance/test_48.png?t=1234')

    def test_icon_url_with_x_and_y(self):
        with self.mocked_path_func:
            from adhocracy.lib import helpers as h
            from adhocracy.tests.testtools import tt_get_instance
            test_instance = tt_get_instance()
            url = h.instance.icon_url(test_instance, 48, x=11)
            self.assertEqual(
                url, 'http://test.test.lan/instance/test_11x48.png?t=1234')

    def test_icon_url_contains_mtime(self):
        with self.mocked_path_func:
            from adhocracy.lib import helpers as h
            from adhocracy.tests.testtools import tt_get_instance
            test_instance = tt_get_instance()
            url = h.instance.icon_url(test_instance, 48)
            self.assertEqual(
                url, 'http://test.test.lan/instance/test_48.png?t=1234')

class TestBaseUrl(TestController):
    def test_base_url_absolute(self):
        from adhocracy.lib.helpers import base_url
        self.assertTrue(u'/' in base_url())
        self.assertTrue(base_url(absolute=True).startswith(u'http'))
