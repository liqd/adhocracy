import base64
import json
import hashlib
import hmac
import logging
import pylons.i18n.translation


__all__ = ["SignedValueConverter"]

log = logging.getLogger(name=__name__)


def _encode_json(o):
    def default(o):
        if isinstance(o, pylons.i18n.translation.LazyString):
            return o.eval()
        return o
    return json.dumps(o, default=default)


try:
    from hmac import compare_digest
except ImportError:  # Python < 3.3
    def compare_digest(a, b):
        if type(a) != type(b) or len(a) != len(b):
            # This conforms to the doc, which says:
            # > If a and b are of different lengths, or if an error occurs, a
            # > timing attack could theoretically reveal information about the
            # > types and lengths of a and b - but not their values.
            return False
        res = 1
        for achar, bchar in zip(a, b):
            # The "and" operator short-circuits!
            res = res & int(achar == bchar)
        return res == 1


class SignedValueConverter(object):
    def __init__(self, secret):
        self._secret = (secret
                        if isinstance(secret, bytes)
                        else secret.encode('ascii'))

    def _sign(self, byte_val):
        assert isinstance(self._secret, bytes)
        assert isinstance(byte_val, bytes)
        hm = hmac.new(self._secret, byte_val, hashlib.sha256)
        digest = hm.hexdigest()
        return digest.encode('ascii') + u'!' + byte_val.encode('ascii')

    def encode(self, value):
        byte_val = base64.b64encode(_encode_json(value))
        return self._sign(byte_val)

    def decode(self, s):
        signature_str, _, enc_val = s.partition(u'!')
        signature = signature_str.encode('ascii')
        byte_val = enc_val.encode('ascii')
        correct_signature = self._sign(byte_val)
        if compare_digest(signature, correct_signature):
            log.debug(u'cookie conversion failed: Signature did not match')
            return None
        return json.loads(base64.b64decode(byte_val))
