
from adhocracy.tests import TestController
import adhocracy.lib.requestlog

class RequestLogTest(TestController):
    def test_anonymization_trivial(self):
        no_anonymization = adhocracy.lib.requestlog.ANONYMIZATION_FUNCS['none']
        self.assertEqual(no_anonymization(u'::1'), u'::1')
        self.assertEqual(no_anonymization(u'127.8.3.2'), u'127.8.3.2')

        dontlog = adhocracy.lib.requestlog.ANONYMIZATION_FUNCS['dontlog']
        self.assertEqual(dontlog('::1'), None)
        self.assertEqual(dontlog(u'127.8.3.2'), None)

    def test_anonymization(self):
        af = adhocracy.lib.requestlog.ANONYMIZATION_FUNCS['anonymize']
        self.assertEqual(af('9.8.3.3'), '9.8.3.0')
        self.assertEqual(af('12.234.122.254'), '12.234.122.0')
        self.assertEqual(af('2001:6f8:1377:2a11:1:2:3:4567'), '2001:6f8:1377:2a11::')
        self.assertEqual(af('2001:6f8:1377:2a11:1:2::4567'), '2001:6f8:1377:2a11::')
        self.assertEqual(af('2001:6f8:1377:2a11::fe:1.2.3.4'), '2001:6f8:1377:2a11::')
        self.assertEqual(af('2001::1377:2a11::fe:1.2.3.4'), '2001:0:1377:2a11::')
        self.assertEqual(af('::ffff:12.234.122.254'), '12.234.122.0')
