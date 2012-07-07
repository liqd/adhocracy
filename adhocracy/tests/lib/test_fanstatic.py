from unittest import TestCase


class TestFanstaticHelpers(TestCase):

    def test_resource(self):
        from adhocracy.lib.helpers.fanstatic_helper import FanstaticNeedHelper
        import fanstatic_dummy_module
        need = FanstaticNeedHelper(fanstatic_dummy_module)
        result = need.resource
        self.assertEqual(result, 'needed resource')

    def test_group(self):
        from adhocracy.lib.helpers.fanstatic_helper import FanstaticNeedHelper
        import fanstatic_dummy_module
        need = FanstaticNeedHelper(fanstatic_dummy_module)
        result = need.group
        self.assertEqual(result, 'needed group')

    def test_not_group_or_resource(self):
        from adhocracy.lib.helpers.fanstatic_helper import FanstaticNeedHelper
        import fanstatic_dummy_module
        need = FanstaticNeedHelper(fanstatic_dummy_module)
        self.assertRaises(ValueError, getattr, need, 'library')

    def test_non_existent_resource(self):
        from adhocracy.lib.helpers.fanstatic_helper import FanstaticNeedHelper
        import fanstatic_dummy_module
        need = FanstaticNeedHelper(fanstatic_dummy_module)
        self.assertRaises(AttributeError, getattr, need, 'nonexistant')
