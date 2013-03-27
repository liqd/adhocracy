from sqlalchemy import MetaData, Table


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)

    user_table = Table('user', meta, autoload=True)
    user_table.c.password.alter(nullable=True)


def downgrade(migrate_engine):
    raise NotImplementedError()
