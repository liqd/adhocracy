from sqlalchemy import MetaData
from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy import Boolean, Integer, Unicode

metadata = MetaData()


page_table = Table(
    'page', metadata,
    Column('id', Integer, ForeignKey('delegateable.id'), primary_key=True),
    Column('function', Unicode(20)),
)


def upgrade(migrate_engine):
    metadata.bind = migrate_engine

    page_formatting = Column('formatting', Boolean, default=False)
    page_formatting.create(page_table)

    from adhocracy.model import Page
    update = page_table.update().values(formatting=True).where(
        page_table.c.function == Page.DESCRIPTION)
    migrate_engine.execute(update)


def downgrade(migrate_engine):
    raise NotImplementedError()
