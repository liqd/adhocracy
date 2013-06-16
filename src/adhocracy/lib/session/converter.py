from adhocracy.lib.crypto import sign, verify

import base64
import json
import logging
import pylons.i18n.translation


__all__ = ["SignedValueConverter"]

log = logging.getLogger(name=__name__)
_SALT = b'cookie session'


def _encode_json(o):
    def default(o):
        if isinstance(o, pylons.i18n.translation.LazyString):
            return o.eval()
        return o
    return json.dumps(o, default=default)


class SignedValueConverter(object):
    def __init__(self, secret):
        self._secret = secret

    def encode(self, value):
        byte_val = base64.b64encode(_encode_json(value))
        encoded = sign(byte_val, self._secret, _SALT)
        return encoded.decode('ascii')

    def decode(self, s):
        try:
            byte_val = verify(s.encode('ascii'), self._secret, _SALT)
            return json.loads(base64.b64decode(byte_val))
        except ValueError as e:
            log.debug(str(e))
            return None
