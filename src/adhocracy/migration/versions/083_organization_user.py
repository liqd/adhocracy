from sqlalchemy import Column, MetaData, Table
from sqlalchemy import Boolean

metadata = MetaData()


def upgrade(migrate_engine):
    metadata.bind = migrate_engine

    user_table = Table('user', metadata, autoload=True)

    _is_organization = Column('_is_organization',
                              Boolean,
                              nullable=True,
                              default=False)
    _is_organization.create(user_table)


def downgrade(migrate_engine):
    raise NotImplementedError()
