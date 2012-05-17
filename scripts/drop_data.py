#!/usr/bin/env python
"""
Extract email adresses from adhocracy. Emails from deleted users won't be
exported.
"""

# boilerplate code. copy that
import os
import sys
sys.path.insert(0,  os.path.abspath(os.path.dirname(__file__)))
from common import create_parser, load_from_args
# /end boilerplate code

from adhocracy.model import meta


def main():
    parser = create_parser(description=__doc__, use_instance=False)
    parser.add_argument('-f', dest='force', default=False, action='store_true',
                        help="force deletion without asking for confirmation")
    args = parser.parse_args()
    load_from_args(args)

    if not args.force:
        input = raw_input('Delete all data? No backup will be done! '
                          'If so type "yes": ')
        if input != 'yes':
            print 'Answer not "yes", but: "%s"\nAborting.' % input
            exit(1)
    tables = meta.data.tables.keys()
    tables.append('migrate_version')
    tables.append('alternative')  # only existing in very old databases
    for table in tables:
        print 'drop table: %s' % table
        meta.engine.execute('DROP TABLE IF EXISTS "%s" CASCADE' % table)


if __name__ == '__main__':
    sys.exit(main())
