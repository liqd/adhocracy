from adhocracy.lib.session.converter import ValueConverter

__all__ = ["PlainValueConverter"]

class PlainValueConverter(ValueConverter):

    def encode(self, value):
        return self._serialize(value)

    def decode(self, value):
        return self._unserialize(value)
