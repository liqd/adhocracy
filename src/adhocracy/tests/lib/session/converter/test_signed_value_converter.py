from adhocracy.tests import TestController
from adhocracy.lib.session.converter import SignedValueConverter

import json


class SignedValueConverterTestController(TestController):
    _test_string = "Alaska Sadelaere"
    _test_encoded = "Alaska Sadelaere"
    _test_algo = '"algo": "sha256"'
    _test_value = '"value": "{0}"'.format(self._test_encoded)
    _test_sign = '"sign": '

    def signed_value_with_no_secret(self):
        signer = SignedValueConverter()

        val = signer.encode(self._test_string)

        self.assertTrue(
                self._test_algo in val and
                self._test_value in val and
                self._test_sign in val)

    def signed_value_with_secret(self):
        signer = SignedValueConverter("secret")

        val = signer.encode(self._test_string)

        self.assertTrue(
                self._test_algo in val and
                self._test_value in val and
                self._test_sign in val)

    def signed_value_with_invalid_sign(self):
        signer = SignedValueConverter("secret")

        val = signer.encode(self._test_string)

        obj = json.loads(val)
        obj["sign"] = "af8907sajkh32uigfa97asekjejh4l2jk3hf9a87dfa6"

        val = json.dumps(obj)

        self.assertIsNone(signer.decode(val))

    def signed_value_with_no_json(self):
        signer = SignedValueConverter("secret")

        val = "023nlaify90a86afa9s8dv"

        self.assertIsNone(signer.decode(val))

