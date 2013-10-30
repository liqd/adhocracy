#!/usr/bin/env python

import os.path
import unittest

import pep8

SRC_PATH = os.path.dirname(os.path.dirname(__file__))
EXCLUDE = ['.svn', 'CVS', '.bzr', '.hg', '.git',
           'Paste-1.7.5.1-py2.6.egg', 'PasteDeploy-1.5.0-py2.6.egg', 'data']


class AdhocracyStyleGuide(pep8.StyleGuide):
    def ignore_code(self, code):
        IGNORED = [
            'E111',  # indentation is not a multiple of four
            'E121',  # continuation line indentation is not a multiple of four
            'E123',  # closing bracket does not match indentation of opening
                     # bracket
            'E124',  # closing bracket does not match visual indentation
            'E126',  # continuation line over
            'E127',  # continuation line over
            'E128',  # continuation line under
            'E501',  # line too long
        ]
        return code in IGNORED


class TestPep8(unittest.TestCase):
    def test_pep8(self):
        sg = AdhocracyStyleGuide(exclude=EXCLUDE)
        sg.input_dir(SRC_PATH)
        self.assertEqual(sg.options.report.get_count(), 0)
