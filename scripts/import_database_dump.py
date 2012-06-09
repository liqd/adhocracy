#!/usr/bin/env python
"""
Import a dump file from pg_dump into the database specified
in the <config file>.
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
    parser.add_argument('--dump', default=None, required=True,
                        help="Path to the SQL dump file.")
    args = parser.parse_args()

    # check and cleanup dump file
    dump_path = os.path.join(os.getcwd(), args.dump)
    if not os.path.exists(dump_path):
        parser.error('SQL dump file "%s" does not exist.' % args.dump)

    # get an engine to get the driver type and connection details.
    engine = get_engine(config_from_args(args))
    drivername = engine.url.drivername

    error = False
    if drivername == 'postgresql':
        # use the psql command line script for imports.
        # pg_dump by default emits COPY ... FROM STDIN statements
        # which the psycopg2 driver can't handle.
        # pg_dump can emit inserts (--inserts), but that's
        # dead slow to import.
        vars = engine.url.__dict__.copy()
        vars['dump_path'] = dump_path
        command = ('psql -U {username} -h {host} -p {port} -'
                   'd {database} -f {dump_path}').format(**vars)
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
