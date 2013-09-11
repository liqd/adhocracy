"""
adhocracy.lib.core contains helper functions and classes which don't depend on
any libraries outside of standard Python.
"""


class CustomDict(dict):
    """
    Custom dictionary which allows to overwrite the setitem method by
    passing a custom setter to the constructor.

    This is basically copied from
    http://stackoverflow.com/questions/2060972/subclassing-python-dictionary-to-override-setitem  # noqa
    """

    def __init__(self, setter_fun=lambda k, v: (k, v), *args, **kwargs):
        self.setter_fun = setter_fun
        self.update(*args, **kwargs)

    def __setitem__(self, key, value):
        super(CustomDict, self).__setitem__(*self.setter_fun(key, value))

    def update(self, *args, **kwargs):
        if len(args) > 1:
            raise TypeError("update expected at most 1 arguments, got %d"
                            % len(args))
        other = dict(*args, **kwargs)
        for key in other:
            self[key] = other[key]

    def setdefault(self, key, value=None):
        if key not in self:
            self[key] = value
        return self[key]
