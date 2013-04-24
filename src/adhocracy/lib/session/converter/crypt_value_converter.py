try:
    from Crypto import Cipher, Random
except:
    raise ImportError("Need the \"Python Cryptography Toolkit\" installed")

try:
    import hashlib
except:
    raise ImportError("Python version >= 2.5 needed")

from adhocracy.lib.session.converter import ValueConverter


__all__ = ["CryptValueConverter"]

""" This class provides methods to crypt an value and decrypt it with
    a secret that is identical over all requests.
"""
class CryptValueConverter(ValueConverter):
    _secret = None
    _secret_set = False
    _algorithm = Cipher.AES
    _algorithm_id = "AES-CFB"
    _mode = Cipher.AES.MODE_CFB
    _iv = Random.new().read(_algorithm.block_size)
    _func_crypt = None

    def __init__(self, secret=None):
        if not self._secret_set:
            self._secret = self._ensure_secret(secret)

        if not self._func_crypt:
            self._func_crypt = self._algorithm.new(
                    bytes(self._secret),
                    self._mode,
                    self._iv)

    def _ensure_secret(self, secret):
        if not secret:
            secret = Random().read(256)
        elif self._algorithm == Cipher.AES:
            if len(secret) not in [32, 256, 24, 192, 16, 128]:
                secret = hashlib.sha256(secret).hexdigest()[:32]

        return secret

    def _crypt_value(self, value):
        return self._serialize({"value": value, "secret": self._secret})

    def encode(self, value):
        return self._serialize({
                "value": self._func_crypt.encrypt(self._crypt_value(value)),
                "algo": self._algorithm_id})

    def decode(self, value):
        return self._unserialize(
                self._func_crypt.decrypt(
                self._unserialize(value)["value"])
                )["value"]

