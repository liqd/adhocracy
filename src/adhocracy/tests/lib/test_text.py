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
        self.assertTrue(u'<' not in core_result)

    def test_render_markdown_vuln(self):
        from adhocracy.lib.text import render
        source = u'[XSS](javascript://%0Aalert%28\'XSS\'%29;)'
        result = render(source)
        self.assertTrue(u'javascript' not in result)

    def test_html_sanitizing(self):
        from adhocracy.lib.text import render
        source = '<h1>Hello</h1><script>XSS</script>' \
                '<object>include_dangerous</object>' \
                '<embed>include_dangerous</embed>' \
                '<a href="javascript:bar()" onclick="javascript: alert(\'foo\')">lala</a>' \
                '<iframe class="youtube-player" type="text/html" width="640" height="385"' \
                ' src="http://www.youtube.com/embed/foo" frameborder="0">' \
                '</iframe>'
        result = render(source, safe_mode='adhocracy_config', _testing_allow_user_html=True)
        self.assertTrue('<script' not in result)
        self.assertTrue('<object' not in result)
        self.assertTrue('<embed' not in result)
        self.assertTrue('javascript' not in result)
        self.assertTrue('<iframe' in result)

