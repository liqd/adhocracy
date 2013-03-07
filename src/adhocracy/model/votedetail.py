from sqlalchemy import Table, Column
from sqlalchemy import Integer, ForeignKey
from adhocracy.model import meta

votedetail_table = Table(
    'votedetail', meta.data,
    Column('instance_id', Integer,
            ForeignKey('instance.id', ondelete='CASCADE')),
    Column('badge_id', Integer,
            ForeignKey('badge.id', ondelete='CASCADE')),
)
