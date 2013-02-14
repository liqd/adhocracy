#!/usr/bin/env python
# coding: utf-8

import unittest

from adhocracy.controllers.openidauth import is_trusted_provider

class TestOpenIDAuth(unittest.TestCase):
    def test_is_trusted_provider(self):
        self.assertFalse(is_trusted_provider('http://evil.com/openid'))
        
        self.assertTrue(is_trusted_provider('http://1aA-ä-k.myopenid.com/'))
        self.assertTrue(is_trusted_provider('https://1aA-ä-k.myopenid.com'))
        self.assertTrue(is_trusted_provider('https://www.google.com/accounts/o8/id'))
        self.assertTrue(is_trusted_provider('https://me.yahoo.com/foo'))
        self.assertTrue(is_trusted_provider('http://me.yahoo.com'))

        self.assertFalse(is_trusted_provider('http://evil.com/my.myopenid.com/'))
        self.assertFalse(is_trusted_provider('http://my.myopenid.com.evil.com/'))
        self.assertFalse(is_trusted_provider('http://[2001::bad:1]/my.myopenid.com/'))


if __name__ == '__main__':
    unittest.main()
