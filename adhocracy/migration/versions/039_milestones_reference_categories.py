from datetime import datetime
from sqlalchemy import Column, ForeignKey, MetaData, Table
from sqlalchemy import DateTime, Integer, Unicode, UnicodeText


meta = MetaData()

milestone_table = Table(
    'milestone', meta,
    Column('id', Integer, primary_key=True),
    Column('instance_id', Integer, ForeignKey('instance.id'), nullable=False),
    Column('creator_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('title', Unicode(255), nullable=True),
    Column('text', UnicodeText(), nullable=True),
    Column('time', DateTime),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('delete_time', DateTime)
)


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    Table('user', meta, autoload=True)
    Table('instance', meta, autoload=True)
    Table('badge', meta, autoload=True)
    category_column = Column('category_id', Integer, ForeignKey('badge.id'),
                             nullable=True)
    category_column.create(milestone_table)
    modify_time_column = Column('modify_time', DateTime, nullable=True,
                           onupdate=datetime.utcnow)
    modify_time_column.create(milestone_table)


def downgrade(migrate_engine):
    raise NotImplementedError()
