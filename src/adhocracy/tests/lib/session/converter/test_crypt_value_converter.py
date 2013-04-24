from adhocracy.tests import TestController
from adhocracy.lib.session.converter import CryptValueConverter

import json


class CryptValueConverterTestController(TestController):
    _test_string = "䷝Goeffry Abel Waringer⁋"
    _test_encoded = "\\\\u4dddGoeffry Abel Waringer\\\\u204b"
    _test_algo = '"algo": "AES-CFB"'
    _test_value = '"value": '

    def crypt_value_with_no_secret(self):
        cryptor = CryptValueConverter()

        val = cryptor.encode(self._test_string)

        self.assertTrue(self._test_algo in val and self._test_value in val)

        self.assertEqual(cryptor.decode(val), self._test_string)

    def crypt_value_with_secret(self):
        cryptor = CryptValueConverter("secret")

        val = cryptor.encode(self._test_string)

        self.assertTrue(self._test_algo in val and self._test_value in val)

        self.assertEqual(cryptor.decode(val), self._test_string)

    def crypt_value_with_wrong_payload(self):
        cryptor = CryptValueConverter("Setec Astronomy")

        val = cryptor.encode(self._test_string)

        obj = json.loads(obj)
        obj["value"] = "203478uhkfha7d8sv5asj2h3490v8a70977df60a9762lkjh3"

        val = json.dumps(obj)

        self.assertIsNone(cryptor.decode(val))

    def crypt_value_decode_non_json(self):
        cryptor = CryptValueConverter()

        val = "as8dyvasuiodhva890se7ro23ujhraf9078sd6f987g23lkjbbffa89fa"

        self.assertIsNone(cryptor.decode(val))

