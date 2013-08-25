from adhocracy.tests import TestController
import adhocracy.lib.emailcomments.util
import adhocracy.lib.emailcomments.parseincoming
import adhocracy.lib.text.render
from adhocracy.tests import testtools

class EmailParsingTest(TestController):
    def test_render(self):
        '''safe_mode must be False'''
        r = adhocracy.lib.text.render
        self.assertEqual(r(u"![alt](http://test.com/test.jpg \"title\")"), 
        u"""<p><img alt=\"alt\" src=\"http://test.com/test.jpg\" title=\"title\" /></p>""")
        self.assertEqual(r(u"![alt](data:image/png;base64,img \"title\")"), 
        u"""<p><img alt=\"alt\" src=\"data:image/png;base64,img\" title=\"title\" /></p>""")


    def test_delete_signatures(self):
        ds = adhocracy.lib.emailcomments.util.delete_signatures
        self.assertEqual(ds(u'foobar\n__barfoo'), u'foobar')
        self.assertEqual(ds(u'foobar\n--barfoo'), u'foobar')
        self.assertEqual(ds(u'foobar\n __barfoo'), u'foobar\n __barfoo')
        self.assertEqual(ds(u'foobar\n_barfoo'), u'foobar\n_barfoo')
        self.assertEqual(ds(u'foobar\n-----BEGIN PGP SIGNED MESSAGE-----\n'), u'\n')
        self.assertEqual(ds(u'foobar\n-----BEGIN PGP SIGNED MESSAGE-----\nHash: SHA512\n\nbarfoo'), u'barfoo')
        self.assertEqual(ds(u'foobar\nHash: SHA512\n\nbarfoo'), u'foobar\nHash: SHA512\n\nbarfoo')
        self.assertEqual(ds(u"""
some debris...
-----BEGIN PGP SIGNED MESSAGE-----
Hash: SHA1

This is the Payload of
the PGP-signed message.

-----BEGIN PGP SIGNATURE-----
iQA/AwUBONpOg40d+PaAQUTlEQIc5ACdGkKSzpOrsT0Gvj3jH9NXD8ZP2IcAn0vj
/BHT+qQCtPCtCwO1aQ3Xk/NL
=1CZt
-----END PGP SIGNATURE-----

__________________
provider signature"""),

u"""This is the Payload of
the PGP-signed message.
""")


    def test_html_to_markdown(self):
        rp = adhocracy.lib.emailcomments.util.html_to_markdown
        self.assertEqual(rp(u'<br>'), u'  \n')
        self.assertEqual(rp(u'\n\t<br>\t\t\n\n<br>'), u'  \n  \n')
        self.assertEqual(rp(u'<body>foobar<br>\n\nbarfoo</body>'), u'foobar  \nbarfoo')
        self.assertEqual(rp(u'<b> foobar</b>'), u'**foobar**')
        self.assertEqual(rp(u'<h2>foobar</h2>'), u'## foobar  \n')
        self.assertEqual(rp(u'<h2>foobar</h3>'), u'## foobar  \n')
        self.assertEqual(rp(u'<body>foobar<br>\r\n\n\rbarfoo</body>'), u'foobar  \nbarfoo')
        self.assertEqual(rp(u"""<html>
  <head>
    <meta content="text/html; charset=UTF-8" http-equiv="Content-Type">
    <style type="text/css" media="screen">
    body { background-image:url(back.jpg); padding:10px; }
    #bigtext { font-size:150px; font-family:"Arial Black",Arial,sans-serif; color:#73FBE7; }
    #smalltext { font-size:90px; font-family:"Arial Black",Arial,sans-serif; color:#fff; }
    </style>
    <script type="text/javascript">
    function time () {
      some_evil_things;
    }
    </script>
  </head>
  <body text="#000000" bgcolor="#FFFFFF">


    <ul>
    <li>foo
    <li>    bar</li>
    </ul>
    <h3>bla</h3>
    <img src="foo.bar/bar.gif" alt="foo"><br>
    <img src="foo.bar/bar.gif"  >
    <img alt="bar"><br>
    <img><br>
    <i id="some_id" >bar</i><b>bar</b><br>
    <q>foobar</q>
    <blockquote cite="link" class="some_class">bar</blockquote>
    <a href="foobar.de" name="some_name">barfoo</a>
    <br>
    <br >
    <br />
    <br/>
    <bogustag<foobar</bogus>
    <bogustagclass="bog" id="bar"<foobar</bogus>

  </body>
</html>"""),

u"""* foo  
* bar  
  
### bla  
![foo](http://foo.bar/bar.gif "http://foo.bar/bar.gif")  
  
  
*bar***bar**  
  > foobar  

  > bar  

[barfoo](http://foobar.de "http://foobar.de")  
  
  
  
""")


    def test_get_sentiment(self):
        gs = adhocracy.lib.emailcomments.util.get_sentiment
        self.assertEqual(gs(u'vote:+\n'), (u'', 1))
        self.assertEqual(gs(u'vote:+\r\n'), (u'', 1))
        self.assertEqual(gs(u'vote:+\r'), (u'', 1))
        self.assertEqual(gs(u'Vote: 1\nfoo bar'), (u'foo bar', 1))
        self.assertEqual(gs(u'Vote: +1\r\nfoo\nbar'), (u'foo\nbar', 1))
        self.assertEqual(gs(u'0\na'), (u'a', 0))
        self.assertEqual(gs(u'-\nfoo'), (u'foo', -1))
        self.assertEqual(gs(u'anything'), (u'anything', None))
        self.assertEqual(gs(u'Vote: -1\n'), (u'', -1))
        self.assertEqual(gs(u'Vote -1\n'), (u'', -1))
        self.assertEqual(gs(u'2010\n'), (u'2010\n', None))
        self.assertEqual(gs(u'010\n'), (u'010\n', None))
        self.assertEqual(gs(u"""vote     +
The Message"""),
(u"""The Message""", 1))


    def test_content_type_reader(self):
        ctr = adhocracy.lib.emailcomments.util.content_type_reader
        self.assertEqual(ctr(u'image/png'), (u'png', u'png-image'))
        self.assertEqual(ctr(u'image/png; name=foobar.png'), (u'png', u'foobar'))
        self.assertEqual(ctr(u'image/png; name=bar.foobar.png'), (u'png', u'bar.foobar'))


    def test_delete_debris(self):
        dd = adhocracy.lib.emailcomments.util.delete_debris
        self.assertEqual(dd(u'foobar\n\n\n\n'), u'foobar')
        self.assertEqual(dd(u'\n\nfoobar\n\n'), u'foobar')
        self.assertEqual(dd(u'\n  foobar\n  '), u'foobar')
        self.assertEqual(dd(u'  \nfoobar  \n'), u'foobar')
        self.assertEqual(dd(u'  \nfoobar  \n'), u'foobar')
        self.assertEqual(dd(u'\r\n    \n\nfoobar  \r\n   \n\n'), u'foobar')
        self.assertEqual(dd(u'foo\n\n\n\n\nbar'), u'foo\n\nbar')
        self.assertEqual(dd(u' \n  foo\r\n   \n   \n \n\r\nbar \n '), u'foo\n\nbar')


    def test_parse_local_part(self):
        '''test for admin'''
        from pylons import config
        secrets = config.get("adhocracy.crypto.secret")

        comment = testtools.tt_make_comment()

        reply_id = unicode(comment.id)     

        import hashlib
        sec_token = hashlib.sha1(u"1" + reply_id + secrets).hexdigest()

        test_string = (u'subs.1-{0}.{1}@domain.tld').format(reply_id,
                sec_token)

        fail_string = (u'subs.1-{0}.MOCKSECRET@domain.tld').format(reply_id)

        from adhocracy.model import User
        user = User.find(1)

        plp = adhocracy.lib.emailcomments.parseincoming.parse_local_part
        self.assertEqual(plp(u'subs.50-50.foobar@domain.tld'), None)
        self.assertEqual(plp(u'subs.1-1.feb340279618fb47d6c0feb340279618fb47d6c0@domain.tld'),None)
        self.assertEqual(plp(test_string), (user, comment))
        self.assertEqual(plp(fail_string), None)


    def test_remove_notification(self):
        rm = adhocracy.lib.emailcomments.util.remove_notification
        self.assertEqual(rm(u"""first new line
_________________________________
some text here
some text there
_________________________________
some new line"""), u"""first new line
some new line""")
        self.assertEqual(rm(u"""first new line
>_________________________________
>some text here
>some text there
>_________________________________
some new line"""), u"""first new line

some new line""")
        self.assertEqual(rm(u"""first new line
> _________________________________
> some text here
> some text there
> _________________________________
some new line"""), u"""first new line

some new line""")
        self.assertEqual(rm(u"""first new line
foobar> _________________________________
> some text here
> some text there
> _________________________________
some new line"""), u"""first new line
foobar
some new line""")
