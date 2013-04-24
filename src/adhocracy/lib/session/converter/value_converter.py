try:
    import json
except:
    raise ImportError("Python version >= 2.6 needed")


__all__ = ["ValueConverter"]

class ValueConverter(object):

    def __init__(self):
        raise NotImplementedError("This is an abstract class.")

    def _serialize(self, value):
        try:
            return json.dumps(value)
        except:
            return None

    def _unserialize(self, value):
        try:
            return json.loads(value)
        except:
            return None

    def encode(self, value):
        raise NotImplementedError("This is an abstract class.")

    def decode(self, value):
        raise NotImplementedError("This is an abstract class.")

