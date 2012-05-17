#!/usr/bin/env python
"""
Extract email adresses from adhocracy. Emails from deleted users won't be
exported.
"""

# boilerplate code. copy that
import os
import sys
sys.path.insert(0,  os.path.abspath(os.path.dirname(__file__)))
from common import create_parser, config_from_args, get_engine
# /end boilerplate code

import subprocess


def main():
    parser = create_parser(description=__doc__, use_instance=False)
    parser.add_argument('--script', default=None,
                        help="path to the input sql script")
    args = parser.parse_args()

    # check and cleanup script
    script_path = os.path.join(os.getcwd(), args.script)
    if not os.path.exists(script_path):
        parser.error('sql script "%s" does not exist.' % args.script)

    # get a connection and execute the script
    engine = get_engine(config_from_args(args))
    drivername = engine.url.drivername

    error = False
    if drivername == 'postgresql':
        vars = engine.url.__dict__.copy()
        vars['script_path'] = script_path
        command = ('psql -U {username} -h {host} -p {port} -'
                   'd {database} -f {script_path}').format(**vars)
        print 'Executing command: %s' % command
        if engine.url.password is not None:
            print 'Prefixing it with PGPASSWORD="<password>"'
            command = 'PGPASSWORD="%s %s" ' % (engine.url.password, command)

        error = subprocess.call(command, shell=True)
    else:
        print ('Action for driver "%s" is not defined.\n'
               "Note: sqlite3 has a non-standard executescript() method.")
        exit(1)

    if error:
        print 'Process exited with Error: %s' % error
        exit(error)


if __name__ == '__main__':
    sys.exit(main())
