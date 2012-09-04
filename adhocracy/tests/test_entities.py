#!/usr/bin/env python

import codecs, optparse, os, re, sys
import unittest

class TestEntities(unittest.TestCase):
    
    def test_template_dir(self):
        process_path(os.path.join(os.path.dirname(__file__), '../templates'))

DEFAULT_EXTENSION = '.html'

def find_files(path, ext):
    """Find files recursively with a given file extension"""
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(ext):
                yield os.path.join(root, file)

def process_file(fn):
    with open(fn, 'rb') as f:
        try:
            absfn = os.path.abspath(fn)
            content = f.read().decode('utf-8')
        except UnicodeDecodeError as e:
            print (absfn + ' is not UTF-8')
            return False

    success = True
    for k in re.finditer('&(?!#|([A-Z]|[a-z])[a-z]{1,5};)', content):
        ln = content[:k.start()].count('\n') + 1
        print ('Invalid entity "' + content[k.start():k.end()+10] + 
               '" found in ' + absfn + ': ' + str(ln))
        success = False
    return success

def process_dir(dir_path, ext):
    for fn in find_files(dir_path, ext):
        process_file(fn)

def process_path(path, ext=DEFAULT_EXTENSION):
    if os.path.isdir(path):
        return process_dir(path, ext)
    else:
        return process_file(path)


def main():
    parser = optparse.OptionParser()
    parser.add_option('-e', action="store", dest="ext", type="string", default=DEFAULT_EXTENSION,
                        help="The file extension of the files you want to check (Only used with -d DIR)")
    (options, paths) = parser.parse_args()

    if not paths:
        paths.append('.')
    for path in paths:
        if not process_path(path, options.ext):
            sys.exit(10)

if __name__ == "__main__":
    main()
