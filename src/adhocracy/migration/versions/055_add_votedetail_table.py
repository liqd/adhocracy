from sqlalchemy import MetaData, Column, Table
from sqlalchemy import Integer, ForeignKey

metadata = MetaData()

votedetail_table = Table(
    'votedetail', metadata,
    Column('instance_id', Integer,
            ForeignKey('instance.id', ondelete='CASCADE')),
    Column('badge_id', Integer,
            ForeignKey('badge.id', ondelete='CASCADE')),
)

def upgrade(migrate_engine):
    meta.bind = migrate_engine
    votedetail_table.create()


def downgrade(migrate_engine):
    raise NotImplementedError()
