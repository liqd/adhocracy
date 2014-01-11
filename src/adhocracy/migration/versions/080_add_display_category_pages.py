from sqlalchemy import Column, MetaData, Table
from sqlalchemy import Boolean

metadata = MetaData()


def upgrade(migrate_engine):
    metadata.bind = migrate_engine

    instance_table = Table('instance', metadata, autoload=True)

    display_category_pages = Column('display_category_pages',
                                    Boolean,
                                    nullable=True,
                                    default=False)
    display_category_pages.create(instance_table)


def downgrade(migrate_engine):
    raise NotImplementedError()
