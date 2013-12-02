from sqlalchemy import MetaData, Table

metadata = MetaData()


def upgrade(migrate_engine):
    metadata.bind = migrate_engine

    table = Table('milestone', metadata, autoload=True)
    update = table.delete().where(table.c.time == None)  # noqa
    migrate_engine.execute(update)

    table.c.time.alter(nullable=False)


def downgrade(migrate_engine):
    raise NotImplementedError()
