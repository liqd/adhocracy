#!/usr/bin/env python

from __future__ import print_function

import optparse
import os
import re
import sys
import unittest

DEFAULT_PATH = os.path.join(os.path.dirname(__file__), '../templates')
DEFAULT_EXTENSION = '.html'


class TestEntities(unittest.TestCase):
    def test_template_dir(self):
        process_path(DEFAULT_PATH, on_error=lambda msg: self.fail(msg))

def find_files(path, ext):
    """Find files recursively with a given file extension"""
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(ext):
                yield os.path.join(root, file)

def process_file(fn, on_error):
    with open(fn, 'rb') as f:
        try:
            absfn = os.path.abspath(fn)
            content = f.read().decode('utf-8')
        except UnicodeDecodeError:
            on_error(absfn + ' is not UTF-8')
            return False

    success = True
    for k in re.finditer('&(?!#|([A-Z]|[a-z])[a-z]{1,5};)', content):
        ln = content[:k.start()].count('\n') + 1
        on_error('Invalid entity "' + content[k.start():k.end()+10] + 
               '" found in ' + absfn + ': ' + str(ln))
        success = False
    return success

def process_dir(dir_path, ext, on_error):
    return all(
        process_file(fn, on_error=on_error)
        for fn in find_files(dir_path, ext)
    )

def process_path(path, ext=DEFAULT_EXTENSION, on_error=print):
    if os.path.isdir(path):
        return process_dir(path, ext, on_error=on_error)
    else:
        return process_file(path, on_error=on_error)


def main():
    parser = optparse.OptionParser('[files-or-dirs...]')
    parser.add_option('-e', action="store", dest="ext", type="string", default=DEFAULT_EXTENSION,
                        help="The file extension of the files you want to check")
    (options, paths) = parser.parse_args()

    if not paths:
        paths.append(DEFAULT_PATH)
    for path in paths:
        if not process_path(path, options.ext):
            sys.exit(10)

if __name__ == "__main__":
    main()
