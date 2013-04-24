try:
    import hashlib
except:
    raise ImportError("Python version >= 2.5 needed")

from adhocracy.lib.session.converter import ValueConverter

import logging


__all__ = ["SignedValueConverter"]

log = logging.getLogger(name=__name__)

class SignedValueConverter(ValueConverter):
    _algorithm = "sha256"
    _secret = None

    def __init__(self, secret):
        self._secret = secret

    def _sign_value(self, value):
        return self._serialize({"value": value, "secret": self._secret})

    def sign(self, value):
        return hashlib.__dict__[self._algorithm](
                self._sign_value(value)).hexdigest()

    def sign_valid(self, value, sign):
        return sign == self.sign(value)

    def encode(self, value):
        return self._serialize({
                "algo": self._algorithm,
                "value": value,
                "sign": self.sign(value)})

    def decode(self, value):
        if self._unserialize(value):
            obj = self._unserialize(value)

            log.debug("decode: unserialize result = {0}".format(obj))
            if self.sign_valid(obj["value"], obj["sign"]):
                log.debug("decode: valid sign for {0}".format(obj["value"]))
                return obj["value"]

        return None

