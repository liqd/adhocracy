'''
Fix an error in the previous migration where wie pickled the versions
into a string that was pickled again by sqlalchemy.
'''
from datetime import datetime
from pickle import loads

from sqlalchemy import (MetaData, Column, ForeignKey, DateTime, Integer,
                        PickleType, Table)

metadata = MetaData()


def are_elements_equal(x, y):
    return x == y


selection_table = Table(
    'selection', metadata,
    Column('id', Integer, primary_key=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('delete_time', DateTime),
    Column('page_id', Integer, ForeignKey('page.id',
           name='selection_page', use_alter=True), nullable=True),
    Column('proposal_id', Integer, ForeignKey('proposal.id',
           name='selection_proposal', use_alter=True), nullable=True),
    Column('variants', PickleType(comparator=are_elements_equal),
           nullable=True)
    )


def upgrade(migrate_engine):

    metadata.bind = migrate_engine

    selections = migrate_engine.execute(selection_table.select())
    fixed = 0
    for (id, _, _, _, _, variants) in selections:
        try:
            # see if we can unpickle from the variants value
            variants = loads(variants)
        except TypeError:
            continue

        if not isinstance(variants, list):
            raise ValueError(
                ("Already fixed: %s. Error in selection %s. 'variants' is "
                 'double pickled, but not a list. Value: %s, type: %s') %
                (id, str(variants), type(variants)))
        fixed += 1
        migrate_engine.execute(
            selection_table.update().values(variants=variants).where(
                selection_table.c.id == id))


def downgrade(migrate_engine):
    raise NotImplementedError()
