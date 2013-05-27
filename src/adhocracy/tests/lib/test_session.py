from adhocracy.lib.session.converter import SignedValueConverter
from adhocracy.tests import TestController


class SessionTest(TestController):
    def test_basic(self):
        c = SignedValueConverter(u'shh!')
        encoded = c.encode({'x': [1]})
        decoded = c.decode(encoded)
        self.assertEqual(decoded, {'x': [1]})

    # https://github.com/hhucn/adhocracy.hhu_theme/issues/305
    def test_lazystring(self):
        from pylons.i18n import _, lazy_ugettext as L_

        c = SignedValueConverter(u'shh!')
        c.encode({u'str': L_(u'Date')})
