# coding: utf-8

from adhocracy.lib.session.converter import SignedValueConverter
from adhocracy.tests import TestController


class SessionTest(TestController):
    def test_basic(self):
        c = SignedValueConverter(b'shh!')
        encoded = c.encode({'x': [1]})
        decoded = c.decode(encoded)
        self.assertEqual(decoded, {'x': [1]})

        c2 = SignedValueConverter(b'shh!')
        encoded2 = c.encode({'x': [1]})
        self.assertEqual(encoded2, encoded)

    def test_invalid(self):
        c = SignedValueConverter(b'shh!')
        self.assertEqual(c.decode('aaaaaaa!e30='), None)
        self.assertEqual(c.decode('e30='), None)

    def test_umlauts(self):
        v = {u'"\'/\\ä↭𝕐': u'"\'/\\ä↭𝕐'}
        c = SignedValueConverter(u'"\'/\\ä↭𝕐'.encode('utf-8'))
        encoded = c.encode(v)
        decoded = c.decode(encoded)
        self.assertEqual(decoded, v)

    # https://github.com/hhucn/adhocracy.hhu_theme/issues/305
    def test_lazystring(self):
        from pylons.i18n import _, lazy_ugettext as L_

        c = SignedValueConverter(b'shh!')
        c.encode({u'str': L_(u'Date')})
