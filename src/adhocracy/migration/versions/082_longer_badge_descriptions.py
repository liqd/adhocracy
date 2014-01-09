from sqlalchemy import Column, MetaData, Table
from sqlalchemy import UnicodeText

metadata = MetaData()


def upgrade(migrate_engine):
    metadata.bind = migrate_engine

    badge_table = Table('badge', metadata, autoload=True)

    long_description = Column('long_description',
                              UnicodeText,
                              default=u'',
                              nullable=True)
    long_description.create(badge_table)


def downgrade(migrate_engine):
    raise NotImplementedError()
