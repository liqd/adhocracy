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
