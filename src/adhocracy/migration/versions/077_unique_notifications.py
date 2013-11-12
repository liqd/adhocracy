from sqlalchemy import MetaData
from migrate.changeset.constraint import UniqueConstraint
from sqlalchemy import Table

metadata = MetaData()


def upgrade(migrate_engine):
    metadata.bind = migrate_engine

    table = Table('notification', metadata, autoload=True)

    cons = UniqueConstraint('event_id', 'user_id', table=table)
    cons.create()


def downgrade(migrate_engine):
    raise NotImplementedError()
