from adhocracy.tests import TestController
from adhocracy.lib.session.converter import ValueConverter


class ValueConverterTestController(TestController):

    def no_initialization(self):
        self.assertRaises(NotImplementedError, ValueConverter)
