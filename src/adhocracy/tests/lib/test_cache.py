from unittest import TestCase

from mock import ANY, MagicMock


class TestEntity(object):

    def __init__(self, id):
        self.id = id

    def __unicode__(self):
        return '<TestEntity:%s>' % self.id

    def __repr__(self):
        return '<TestEntity:%s (__repr__)>' % self.id


test_handlers = {TestEntity: lambda: 'called'}


def test_fn(*args, **kwargs):
    '''
    A dummy function we can pass around.
    '''
    pass


class CacheTaggingManagerTests(TestCase):

    def _make_manager(self):
        from adhocracy.lib.cache import CacheTaggingManager
        manager = CacheTaggingManager(test_handlers)
        manager.new_connection = MagicMock()
        return (manager, manager.new_connection())

    def test_make_tag_uses__unicode__(self):
        manager, connection = self._make_manager()
        entity = MagicMock(spec=TestEntity)
        entity.__unicode__.return_value = '<mocked_unicode>'
        self.assertEqual(manager.make_tag(entity), '<mocked_unicode>')
        print manager.make_tag(entity)

    def test_make_tag_falls_back_to__repr__(self):
        manager, connection = self._make_manager()
        entity = MagicMock(spec=TestEntity)
        entity.__unicode__.return_value = u'youwontsee'
        entity.__unicode__.side_effect = NotImplementedError('boom')

        # unicode was called, but it raised an Error so
        # 'youwontsee' is not the tag
        tag = manager.make_tag(entity)
        self.assertTrue(entity.__unicode__.called)
        self.assertNotEqual(tag, u'youwontsee')

        # but __repr__ was called, wich returns the repr of the mock object
        self.assertTrue("<MagicMock spec='TestEntity'" in tag)

    def test_make_tag_raises_error_if_tag_contains_memory_address(self):
        manager, connection = self._make_manager()
        entity = MagicMock(spec=TestEntity)
        entity.__unicode__.return_value = '<foobar object at 0x12345>'
        self.assertRaises(ValueError, manager.make_tag, entity)

    def test_is_handled_if_class_in_handler(self):
        manager, connection = self._make_manager()
        entity = TestEntity(1)
        self.assertEqual(manager.is_handled(entity), True)

        class UnhandledEntity(TestEntity):
            pass

        unhandled_entity = UnhandledEntity(1)
        self.assertEqual(manager.is_handled(unhandled_entity), False)

    def test_key_generator(self):
        manager, connection = self._make_manager()
        make_key = manager.key_generator('test_namespace', test_fn)
        key = make_key()
        self.assertEqual(key, (u'adhocracy.tests.lib.test_cache:test_fn'
                               '|test_namespace'))

    def test_key_generator_with_arg(self):
        manager, connection = self._make_manager()
        make_key = manager.key_generator('test_namespace', test_fn)
        entity = TestEntity(1)
        key = make_key(entity)
        self.assertEqual(key, (u'adhocracy.tests.lib.test_cache:test_fn'
                               '|test_namespace||<TestEntity:1>'))

    def test_key_generator_with_kwarg(self):
        manager, connection = self._make_manager()
        make_key = manager.key_generator('test_namespace', test_fn)
        entity = TestEntity(1)
        key = make_key(akwarg=entity)
        self.assertEqual(key, (u'adhocracy.tests.lib.test_cache:test_fn'
                               '|test_namespace||akwarg::<TestEntity:1>'))

    def test_key_generator_associates_key_with_tags_if_handled(self):
        manager, connection = self._make_manager()
        manager.make_tag = MagicMock(return_value='<mocked_tag>')
        manager.associate_key_with_tags = MagicMock()
        make_key = manager.key_generator('test_namespace', test_fn)
        entity = TestEntity(1)

        # When we make a key with a handled object the key is associated
        # with the tag.
        key = make_key(entity, entity)
        self.assertEqual(manager.associate_key_with_tags.called, True)
        manager.associate_key_with_tags.assert_called_once_with(
            key, ['<mocked_tag>', '<mocked_tag>'])

    def test_key_generator_doesnt_pass_tags_if_not_handled(self):
        manager, connection = self._make_manager()

        # Force to not handle TestEntity
        manager.is_handled = MagicMock(return_value=False)
        manager.associate_key_with_tags = MagicMock()

        make_key = manager.key_generator('test_namespace', test_fn)
        entity = TestEntity(1)

        # When we make a key with an unhandled object the key is not associated
        # with the tag.
        make_key(entity)
        manager.associate_key_with_tags.assert_called_once_with(ANY, [])

    def test_clear_tag(self):
        manager, connection = self._make_manager()

        manager.make_tag = MagicMock(return_value='<mocked_tag>')
        manager.delete_tag_and_associated_keys = MagicMock()

        # if the object is not handled we do nothing
        manager.is_handled = MagicMock(return_value=False)
        manager.clear_tag('dummy_obj')
        self.assertEqual(manager.delete_tag_and_associated_keys.called, False)

        # if the object is handled we delete the tag and all keys
        manager.is_handled.return_value = True
        manager.clear_tag('dummy_obj')
        manager.delete_tag_and_associated_keys.assert_called_once_with(
            '<mocked_tag>')

    def test_low_level_associate_key_with_tags(self):
        manager, connection = self._make_manager()
        # we use a pipeline as a context manager as a transaction
        transaction = connection.pipeline().__enter__()

        manager.associate_key_with_tags('dummy_key',
                                        ['<dummy_tag_1>', '<dummy_tag_2>'])

        transaction.sadd.assert_any_call('<dummy_tag_1>', 'dummy_key')
        transaction.sadd.assert_any_call('<dummy_tag_2>', 'dummy_key')

    def test_low_level_delete_tag_and_associated_keys(self):
        manager, connection = self._make_manager()

        # we use a pipeline as a context manager as a transaction
        transaction = connection.pipeline().__enter__()
        transaction.smembers.return_value = ['dummy_key_1',
                                             'dummy_key_2',
                                             'dummy_key_3']
        manager.delete_tag_and_associated_keys('<dummy_tag>')

        transaction.smembers.assert_called_once_with('<dummy_tag>')
        transaction.delete.assert_any_call('<dummy_tag>')
        transaction.delete.assert_any_call('dummy_key_1', 'dummy_key_2',
                                           'dummy_key_3')
