from datetime import datetime
from sqlalchemy import Column, ForeignKey, MetaData, Table
from sqlalchemy import Boolean, DateTime, Integer, Unicode, UnicodeText

meta = MetaData()

user_table = Table('user', meta)

group_table = Table('group', meta)

delegateable_table = Table('delegateable', meta)

page_table = Table('page', meta)


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    text_table = Table(
        'text', meta,
        Column('id', Integer, primary_key=True),
        Column('page_id', Integer, ForeignKey('page.id'), nullable=False),
        Column('user_id', Integer, ForeignKey('user.id'), nullable=False),
        Column('parent_id', Integer, ForeignKey('text.id'), nullable=True),
        Column('variant', Unicode(255), nullable=True),
        Column('title', Unicode(255), nullable=True),
        Column('text', UnicodeText(), nullable=True),
        Column('create_time', DateTime, default=datetime.utcnow),
        Column('delete_time', DateTime)
        )

    wiki = Column('wiki', Boolean, default=False)
    wiki.create(text_table)
    u = text_table.update(values={'wiki': False})
    migrate_engine.execute(u)


def downgrade(migrate_engine):
    raise NotImplementedError()
