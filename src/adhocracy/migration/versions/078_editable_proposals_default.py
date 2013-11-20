from sqlalchemy import Column, MetaData, Table
from sqlalchemy import Boolean

metadata = MetaData()


def upgrade(migrate_engine):
    metadata.bind = migrate_engine

    instance_table = Table('instance', metadata, autoload=True)

    editable_proposals = Column('editable_proposals_default',
                                Boolean,
                                nullable=True,
                                default=True)
    editable_proposals.create(instance_table)


def downgrade(migrate_engine):
    raise NotImplementedError()
