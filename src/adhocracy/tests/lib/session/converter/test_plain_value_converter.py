from adhocracy.tests import TestController
from adhocracy.lib.session.converter import PlainValueConverter

class PlainValueConverterTestController(TestController):
    _test_string = "Gucky፨"
    _test_encoded = "\"Gucky\\\\u1368\""
    _test_wrong_string = "Julian Tifflor"

    def plain_value_with_no_secret(self):
        converter = PlainValueConverter()

        self.assertEqual(converter.encode(self._test_string), self._test_encoded)

        self.assertIsNone(converter.decode(self._test_wrong_string))

