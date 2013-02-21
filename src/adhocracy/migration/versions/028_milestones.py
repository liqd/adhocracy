from datetime import datetime
from sqlalchemy import Column, ForeignKey, MetaData, Table, Float
from sqlalchemy import Boolean, DateTime, Integer, Unicode, UnicodeText
from sqlalchemy import func, or_

meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine

    user_table = Table('user', meta, autoload=True)
    instance_table = Table('instance', meta, autoload=True)
    delegateable_table = Table('delegateable', meta, autoload=True)

    milestone_table = Table('milestone', meta,
        Column('id', Integer, primary_key=True),
        Column('instance_id', Integer, ForeignKey('instance.id'), nullable=False),
        Column('creator_id', Integer, ForeignKey('user.id'), nullable=False),
        Column('title', Unicode(255), nullable=True),
        Column('text', UnicodeText(), nullable=True),
        Column('time', DateTime),
        Column('create_time', DateTime, default=datetime.utcnow),
        Column('delete_time', DateTime)
        )
    milestone_table.create()
    ms_col = Column('milestone_id', Integer, ForeignKey('milestone.id'), nullable=True)
    ms_col.create(delegateable_table)

    ms_bool = Column('milestones', Boolean, default=False)
    ms_bool.create(instance_table)
    u = instance_table.update(values={'milestones': False})
    migrate_engine.execute(u)


def downgrade(migrate_engine):
    raise NotImplementedError()



