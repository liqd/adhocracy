#!/usr/bin/env python

import codecs, optparse, os, re, sys

default_extension = '.html'
error_string_expansion = 10

def find_files(path, ext):
    """Find files recursively with a given file extension"""
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(ext):
                yield os.path.join(root, file)

def validate_xml_entities(xml_string, xml_name, print_errors=True):
    if xml_string is None:
        return False
    success = True
    for k in re.finditer('&(?!#|[a-z]{2,6};)', xml_string):
        ln = xml_string[:k.start()].count('\n') + 1
        if print_errors:
            print ('Invalid entity "' + xml_string[k.start():k.end()+error_string_expansion] + '" found in ' + xml_name + ' :' + str(ln))
        success = False
    return success

def read_utf8(fn, print_error=True):
    with open(fn, 'rb') as f:
        try:
            return f.read().decode('utf-8')
        except UnicodeDecodeError as e:
            if print_error:
                print (fn + ' is not strict UTF-8')
            return None

def process_file(fn):
    return validate_xml_entities(read_utf8(fn), fn)

def process_dir(dir_path, ext=default_extension):
    for fn in find_files(dir_path, ext):
        process_file(fn)

def main():
    parser = optparse.OptionParser()
    parser.add_option('-d', action="store", dest="dir", type="string", 
                        help="All files with a given extension (-e '.xml' e.g., default is .html) in the dir will be validated")
    parser.add_option('-f', action="store", dest="filename", type="string",
                        help="Validates a single file")
    parser.add_option('-e', action="store", dest="ext", type="string", default=default_extension,
                        help="The file extension you want to search for (Only used with -d DIR)")
    (options, args) = parser.parse_args()

    if not options.dir and not options.filename:
        parser.error('Type -h for usage')
    else:
        if options.dir:
            if os.path.isdir(options.dir):
                print ('Processing all files with the extension ' + options.ext + ' in ' + options.dir + ' ...')
                process_dir(options.dir, options.ext)
            else:
                print ('The given dir path does not represent an existing directory')
        if options.filename:
            if os.path.isfile(options.filename):
                print ('Processing file ' + options.filename + ' ...')
                process_file(options.filename)
            else:
                print ('The given file path does not exist')

if __name__ == "__main__":
    sys.exit(main())
