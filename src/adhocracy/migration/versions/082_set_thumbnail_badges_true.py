from sqlalchemy import MetaData, Table

metadata = MetaData()


def upgrade(migrate_engine):
    metadata.bind = migrate_engine

    table = Table('instance', metadata, autoload=True)
    update = table.update().values(allow_thumbnailbadges=True)
    migrate_engine.execute(update)


def downgrade(migrate_engine):
    raise NotImplementedError()
