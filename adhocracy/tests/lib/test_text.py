from adhocracy.tests import TestController
from adhocracy.tests.testtools import tt_make_user


class TestText(TestController):

    def test_render(self):
        from adhocracy.lib.text import render
        source = ('header\n'
                  '========')
        result = render(source)
        self.assertEqual(result, u'<h1>header</h1>')

    def test_render_no_substitution(self):
        from adhocracy.lib.text import render
        tt_make_user('pudo')
        source = '@pudo'
        result = render(source, substitutions=False)
        self.assertEqual(result, u'<p>@pudo</p>')

    def test_render_user_substitution(self):
        from adhocracy.lib.text import render
        tt_make_user('pudo')
        source = '@pudo'
        result = render(source, substitutions=True)
        self.assertTrue(u'/user/pudo"' in result)

    def test_render_no_xss(self):
        from adhocracy.lib.text import render
        source = '<script>XSS</script><a></a>'
        result = render(source, substitutions=False)
        self.assertEquals(result[:3], '<p>')
        self.assertEquals(result[-4:], '</p>')
        core_result = result[3:-4]
        self.assertTrue(u'<' not in core_result)

    def test_render_no_xss_substitutions(self):
        from adhocracy.lib.text import render
        tt_make_user('<foo>')
        source = '@<foo>'
        result = render(source, substitutions=True)
        self.assertEquals(result[:3], '<p>')
        self.assertEquals(result[-4:], '</p>')
        core_result = result[3:-4]
        print(core_result)
        self.assertTrue(u'<' not in core_result)

    def test_assure_sanitizing(self):
        from adhocracy.lib.text import render
        source = '<h1>Hello</h1><script>XSS</script>'\
                 '<a href="#" onclick="javascript: alert(\'foo\')">lala</a>'
        result = render(source, safe_mode=False)
        self.assertNotIn('<script>', result)
        self.assertNotIn('javascript', result)
