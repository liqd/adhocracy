from unittest import TestCase


class TestVisiblePages(TestCase):
    '''
    Test the functionality of :func:`adhocracy.lib.pager.visible_pages`
    '''

    def test_few_pages(self):
        from adhocracy.lib.pager import visible_pages

        visible, seperators = visible_pages(1, 3)
        self.assertEqual(visible, [1, 2, 3])
        self.assertEqual(seperators, [])

        visible, seperators = visible_pages(2, 3)
        self.assertEqual(visible, [1, 2, 3])
        self.assertEqual(seperators, [])

        visible, seperators = visible_pages(3, 3)
        self.assertEqual(visible, [1, 2, 3])
        self.assertEqual(seperators, [])

    def test_max_displayed_pages(self):
        '''
        If we have the maximum number (11)of pages, we don't need
        seperators
        '''
        from adhocracy.lib.pager import visible_pages

        visible, seperators = visible_pages(1, 11)
        self.assertEqual(visible, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11])
        self.assertEqual(seperators, [])

        visible, seperators = visible_pages(5, 11)
        self.assertEqual(visible, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11])
        self.assertEqual(seperators, [])

        visible, seperators = visible_pages(11, 11)
        self.assertEqual(visible, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11])
        self.assertEqual(seperators, [])

    def test_gt_max_displayed_pages(self):
        '''
        If we have the maximum number (11)of pages, we don't need
        seperators
        '''
        from adhocracy.lib.pager import visible_pages

        visible, seperators = visible_pages(1, 20)
        self.assertEqual(visible, [1, 2, 3, 4, 5, 6, 7, 8, 9, 20])
        self.assertEqual(seperators, [10])

        visible, seperators = visible_pages(7, 20)
        self.assertEqual(visible, [1, 2, 3, 4, 5, 6, 7, 8, 9, 20])
        self.assertEqual(seperators, [10])

        visible, seperators = visible_pages(11, 20)
        self.assertEqual(visible, [1, 8, 9, 10, 11, 12, 13, 14, 20])
        self.assertEqual(seperators, [2, 20])

        visible, seperators = visible_pages(12, 20)
        self.assertEqual(visible, [1, 9, 10, 11, 12, 13, 14, 15, 20])
        self.assertEqual(seperators, [2, 20])

        visible, seperators = visible_pages(13, 20)
        self.assertEqual(visible, [1, 12, 13, 14, 15, 16, 17, 18, 19, 20])
        self.assertEqual(seperators, [2])


class TestSolrTokenHelpers(TestCase):

    def test_entity_to_solr_token_with_hierachy(self):
        from adhocracy.model import CategoryBadge
        from adhocracy.lib.pager import entity_to_solr_token
        badge0 = CategoryBadge.create('testbadge0', '#ccc', True, 'descr')
        badge11 = CategoryBadge.create('testbadge11', '#ccc', True, 'descr')
        badge12 = CategoryBadge.create('testbadge12', '#ccc', True, 'descr')
        badge121 = CategoryBadge.create('testbadge121', '#ccc', True, 'descr')
        badge11.parent = badge0
        badge12.parent = badge0
        badge121.parent = badge12
        result = entity_to_solr_token(badge121)
        shouldbe = u"%s/%s/%s" % (str(badge0.id), str(badge12.id),
                                  str(badge121.id))
        self.assertEqual(result, shouldbe)

    def test_entity_to_solr_token_no_hierachy(self):
        from adhocracy.model import UserBadge
        from adhocracy.lib.pager import entity_to_solr_token
        badge = UserBadge.create('testbadge', '#ccc', True, 'description')
        result = entity_to_solr_token(badge)
        shouldbe = u"%s" % str(badge.id)
        self.assertEqual(result, shouldbe)

    def test_solr_token_to_entity_with_hierachy(self):
        from adhocracy.model import CategoryBadge
        from adhocracy.lib.pager import solr_tokens_to_entities
        badge = CategoryBadge.create('testbadge', '#ccc', True, 'description')
        token = u"1/2/%s" % str(badge.id)
        self.assertEqual(solr_tokens_to_entities([token], CategoryBadge), [badge])

    def test_solr_token_to_entity_no_hierachy(self):
        from adhocracy.model import CategoryBadge
        from adhocracy.lib.pager import solr_tokens_to_entities
        badge = CategoryBadge.create('testbadge', '#ccc', True, 'description')
        token = u"%s" % str(badge.id)
        self.assertEqual(solr_tokens_to_entities([token], CategoryBadge), [badge])
        wrongtoken = "1A"
        self.assertEqual(solr_tokens_to_entities([wrongtoken], CategoryBadge), [])
