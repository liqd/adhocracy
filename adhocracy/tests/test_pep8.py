#!/usr/bin/env python

import os.path
import unittest

import pep8

SRC_PATH = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
EXCLUDE = ['.svn', 'CVS', '.bzr', '.hg', '.git',
           'Paste-1.7.5.1-py2.6.egg', 'PasteDeploy-1.5.0-py2.6.egg', 'data']


class AdhocracyStyleGuide(pep8.StyleGuide):
    def ignore_code(self, code):
        IGNORED = [
            'E111',  # indentation is not a multiple of four
            'E121',  # continuation line indentation is not a multiple of four
            'E122',  # continuation line missing indentation or outdented
            'E123',  # closing bracket does not match indentation of opening
                     # bracket
            'E124',  # closing bracket does not match visual indentation
            'E126',  # continuation line over
            'E127',  # continuation line over
            'E128',  # continuation line under
            'E225',  # missing whitespace around operator
            'E226',  # missing optional whitespace around operator
            'E231',  # missing whitespace after
            'E241',  # multiple spaces after
            'E251',  # no spaces around keyword
            'E261',  # at least two spaces before inline comment
            'E301',  # expected 1 blank line
            'E302',  # expected 2 blank lines
            'E303',  # too many blank lines
            'E501',  # line too long
            'E701',  # multiple statements on one line
            'E702',  # multiple statements on one line
            'E711',  # comparison to None should be 'if cond is None:'
            'E712',  # comparison to True should be 'if cond is True:' or
                     # 'if cond:'
            'W291',  # trailing whitespace
            'W292',  # no newline at end of file
            'W293',  # blank line contains whitespace
            'W391',  # blank line at end of file
        ]
        return code in IGNORED


class TestPep8(unittest.TestCase):
    def test_pep8(self):
        sg = AdhocracyStyleGuide(exclude=EXCLUDE)
        sg.input_dir(SRC_PATH)
        self.assertEqual(sg.options.report.get_count(), 0)
