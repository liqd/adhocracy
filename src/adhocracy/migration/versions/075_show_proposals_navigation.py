from sqlalchemy import MetaData
from sqlalchemy import Column, ForeignKey, Table, func
from sqlalchemy import Boolean, DateTime, Float, Integer, Unicode, UnicodeText

metadata = MetaData()


def upgrade(migrate_engine):
    metadata.bind = migrate_engine

    instance_table = Table('instance', metadata, autoload=True)
    show_norms_navigation = Column('show_proposals_navigation',
                                   Boolean,
                                   default=True)
    show_norms_navigation.create(instance_table)


def downgrade(migrate_engine):
    raise NotImplementedError()
