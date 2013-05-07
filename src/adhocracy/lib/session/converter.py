import base64
import json
import hashlib
import logging


__all__ = ["SignedValueConverter"]

log = logging.getLogger(name=__name__)

class SignedValueConverter(object):
    def __init__(self, secret):
        self._secret = secret

    def _sign(self, enc_value):
        b = self._secret + enc_value
        return getattr(hashlib, u'sha256')(b).hexdigest()

    def encode(self, value):
        enc_value = base64.b64encode(json.dumps(value))
        signature = self._sign(enc_value)
        return signature + u'!' + enc_value

    def decode(self, s):
        signature,_,enc_value = s.partition(u'!')
        correct_signature = self._sign(enc_value)
        if signature != correct_signature:
            log.debug(u'cookie conversion failed: Signature did not match')
            return None
        return json.loads(base64.b64decode(enc_value))

