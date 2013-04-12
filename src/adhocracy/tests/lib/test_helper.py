# -*- coding: utf-8 -*-
from adhocracy.tests import TestController


TEST_IMAGE = (
    'GIF89a\x10\x00\x10\x00\xd5\x00\x00\xff\xff\xff\xff\xff\xfe\xfc\xfd\xfd'
    '\xfa\xfb\xfc\xf7\xf9\xfa\xf5\xf8\xf9\xf3\xf6\xf8\xf2\xf5\xf7\xf0\xf4\xf6'
    '\xeb\xf1\xf3\xe5\xed\xef\xde\xe8\xeb\xdc\xe6\xea\xd9\xe4\xe8\xd7\xe2\xe6'
    '\xd2\xdf\xe3\xd0\xdd\xe3\xcd\xdc\xe1\xcb\xda\xdf\xc9\xd9\xdf\xc8\xd8\xdd'
    '\xc6\xd7\xdc\xc4\xd6\xdc\xc3\xd4\xda\xc2\xd3\xd9\xc1\xd3\xd9\xc0\xd2\xd9'
    '\xbd\xd1\xd8\xbd\xd0\xd7\xbc\xcf\xd7\xbb\xcf\xd6\xbb\xce\xd5\xb9\xcd\xd4'
    '\xb6\xcc\xd4\xb6\xcb\xd3\xb5\xcb\xd2\xb4\xca\xd1\xb2\xc8\xd0\xb1\xc7\xd0'
    '\xb0\xc7\xcf\xaf\xc6\xce\xae\xc4\xce\xad\xc4\xcd\xab\xc3\xcc\xa9\xc2\xcb'
    '\xa8\xc1\xca\xa6\xc0\xc9\xa4\xbe\xc8\xa2\xbd\xc7\xa0\xbb\xc5\x9e\xba\xc4'
    '\x9b\xbf\xcc\x98\xb6\xc1\x8d\xae\xbaFgs\x00\x00\x00\x00\x00\x00\x00\x00'
    '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    '\x00,\x00\x00\x00\x00\x10\x00\x10\x00\x00\x06z@\x80pH,\x12k\xc8$\xd2f\x04'
    '\xd4\x84\x01\x01\xe1\xf0d\x16\x9f\x80A\x01\x91\xc0ZmL\xb0\xcd\x00V\xd4'
    '\xc4a\x87z\xed\xb0-\x1a\xb3\xb8\x95\xbdf8\x1e\x11\xca,MoC$\x15\x18{'
    '\x006}m\x13\x16\x1a\x1f\x83\x85}6\x17\x1b $\x83\x00\x86\x19\x1d!%)\x8c'
    '\x866#\'+.\x8ca`\x1c`(,/1\x94B5\x19\x1e"&*-024\xacNq\xba\xbb\xb8h\xbeb'
    '\x00A\x00;'
)


class TestBadgeHelper(TestController):

    def test_generate_thumbnail_tag_no_color_no_thumb_attr(self):
        from adhocracy.model import ThumbnailBadge
        from adhocracy.lib.helpers.badge_helper import generate_thumbnail_tag
        badge = ThumbnailBadge.create('testbadge0', '', True, 'descr')
        image = generate_thumbnail_tag(badge)
        self.assert_(b'b96ZYAAAAASUVORK5CYII=' in image)

    def test_generate_thumbnail_tag_with_color_attr(self):
        from adhocracy.model import ThumbnailBadge
        from adhocracy.lib.helpers.badge_helper import generate_thumbnail_tag
        badge = ThumbnailBadge.create('testbadge0', '#ccc', True, 'descr')
        image = generate_thumbnail_tag(badge)
        self.assert_(b'Afb96ZYAAAAASUVORK5CYII=' in image)

    def test_generate_thumbnail_tag_with_thumb_attr(self):
        from adhocracy.model import ThumbnailBadge
        from adhocracy.lib.helpers.badge_helper import generate_thumbnail_tag
        badge = ThumbnailBadge.create('testbadge0', '#ccc', True, 'descr')
        badge.thumbnail = TEST_IMAGE
        image = generate_thumbnail_tag(badge)
        self.assert_(b'VWyKXFMAAAAASUVORK5CYII=' in image)

    def test_generate_thumbnail_tag_set_size(self):
        from adhocracy.model import ThumbnailBadge, Instance
        from adhocracy.lib.helpers.badge_helper import generate_thumbnail_tag
        instance = Instance.find(u'test')
        badge = ThumbnailBadge.create('testbadge0', '', True, 'descr')
        badge.instance = instance
        image = generate_thumbnail_tag(badge)
        self.assert_('width="48"' in image)
        self.assert_('height="48"' in image)
        instance.thumbnailbadges_width = 10
        instance.thumbnailbadges_height = 12
        image = generate_thumbnail_tag(badge)
        self.assert_('height="12"' in image)
        self.assert_('width="10"' in image)
        image = generate_thumbnail_tag(badge, width=8, height=11)
        self.assert_('height="11"' in image)
        self.assert_('width="8"' in image)

    def test_generate_thumbnail_cache(self):
        from adhocracy.model import ThumbnailBadge
        from adhocracy.lib.helpers.badge_helper import generate_thumbnail_tag
        badge = ThumbnailBadge.create('testbadge0', '', True, 'descr')
        image = generate_thumbnail_tag(badge)
        self.assert_(b'fb96ZYAAAAASUVORK5CYII=' in image)
        badge.thumbnail = TEST_IMAGE
        image = generate_thumbnail_tag(badge)
        self.assert_(b'VWyKXFMAAAAASUVORK5CYII=' in image)
        badge.thumbnail = "Wrong Data"
        image = generate_thumbnail_tag(badge)
        self.assert_(b'fb96ZYAAAAASUVORK5CYII=' in image)

    def test_get_parent_badges_no_hierarchy(self):
        from adhocracy.model import UserBadge
        from adhocracy.lib.helpers.badge_helper import get_parent_badges
        badge = UserBadge.create('testbadge', '#ccc', True, 'description')
        result = [b.title for b in get_parent_badges(badge)]
        shouldbe = []
        self.assertEqual(result, shouldbe)

    def test_get_parent_badges_with_hierarchy(self):
        from adhocracy.model import CategoryBadge
        from adhocracy.lib.helpers.badge_helper import get_parent_badges
        badge0 = CategoryBadge.create('testbadge0', '#ccc', True, 'descr')
        badge11 = CategoryBadge.create('testbadge11', '#ccc', True, 'descr')
        badge12 = CategoryBadge.create('testbadge12', '#ccc', True, 'descr')
        badge121 = CategoryBadge.create('testbadge121', '#ccc', True, 'descr')
        badge11.parent = badge0
        badge12.parent = badge0
        badge121.parent = badge12
        result = [b.title for b in get_parent_badges(badge121)]
        shouldbe = ['testbadge12', 'testbadge0']
        self.assertEqual(result, shouldbe)
