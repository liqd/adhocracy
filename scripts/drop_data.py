#!/usr/bin/env python
"""
Drop all tables from the database specified in the <config file>
"""

# boilerplate code. copy that
import os
import sys
sys.path.insert(0,  os.path.abspath(os.path.dirname(__file__)))
# /end boilerplate code

from sqlalchemy.engine import reflection
from sqlalchemy.schema import (MetaData, Table, DropTable,
                               ForeignKeyConstraint, DropConstraint)

from common import create_parser, config_from_args, get_engine


def main():
    parser = create_parser(description=__doc__, use_instance=False)
    parser.add_argument('-f', dest='force', default=False, action='store_true',
                        help="force deletion without asking for confirmation")
    args = parser.parse_args()

    if not args.force:
        input = raw_input('Delete all data? No backup will be done! '
                          'If so type "yes": ')
        if input != 'yes':
            print 'Answer not "yes", but: "%s"\nAborting.' % input
            exit(1)

    config = config_from_args(args)
    engine = get_engine(config, echo=True)
    conn = engine.connect()

    # the transaction only applies if the DB supports
    # transactional DDL, i.e. Postgresql, MS SQL Server
    trans = conn.begin()

    inspector = reflection.Inspector.from_engine(engine)

    # gather all data first before dropping anything.
    # some DBs lock after things have been dropped in
    # a transaction.

    metadata = MetaData()

    tbs = []
    all_fks = []

    for table_name in inspector.get_table_names():
        fks = []
        for fk in inspector.get_foreign_keys(table_name):
            if not fk['name']:
                continue
            fks.append(
                ForeignKeyConstraint((), (), name=fk['name'])
                )
        t = Table(table_name, metadata, *fks)
        tbs.append(t)
        all_fks.extend(fks)

    for fkc in all_fks:
        conn.execute(DropConstraint(fkc))

    for table in tbs:
        conn.execute(DropTable(table))

    trans.commit()

if __name__ == '__main__':
    sys.exit(main())
