from sqlalchemy import MetaData, Table


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)

    comment_table = Table('comment', meta, autoload=True)
    comment_table.c.variant.alter(nullable=False)


def downgrade(migrate_engine):
    raise NotImplementedError()
