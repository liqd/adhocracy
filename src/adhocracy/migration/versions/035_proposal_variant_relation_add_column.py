from datetime import datetime

from sqlalchemy import (MetaData, Column, ForeignKey, DateTime, Integer,
                        PickleType, Table)

metadata = MetaData()


selection_table = Table(
    'selection', metadata,
    Column('id', Integer, primary_key=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('delete_time', DateTime),
    Column('page_id', Integer, ForeignKey('page.id',
           name='selection_page', use_alter=True), nullable=True),
    Column('proposal_id', Integer, ForeignKey('proposal.id',
           name='selection_proposal', use_alter=True), nullable=True),
    )


def are_elements_equal(x, y):
    return x == y


def upgrade(migrate_engine):
    metadata.bind = migrate_engine
    page_table = Table('page', metadata, autoload=True)
    proposal_table = Table('proposal', metadata, autoload=True)
    #delegateable_table = Table('delegateable', metadata, autoload=True)

    new_column = Column('variants', PickleType(comparator=are_elements_equal),
                        nullable=True)

    new_column.create(selection_table)


def downgrade(migrate_engine):
    raise NotImplementedError()
