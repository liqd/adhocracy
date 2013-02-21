from datetime import datetime

from sqlalchemy import MetaData, Column, ForeignKey, Table
from sqlalchemy import DateTime, Integer, Unicode, UnicodeText

metadata = MetaData()

old_revision_table = Table('revision', metadata,
    Column('id', Integer, primary_key=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('text', UnicodeText(), nullable=False),
    Column('sentiment', Integer, default=0),
    Column('user_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('comment_id', Integer, ForeignKey('comment.id'), nullable=False),
    Column('title', Unicode(255), nullable=True)
    )


def upgrade(migrate_engine):
    metadata.bind = migrate_engine
    revisions_table = Table('revision', metadata, autoload=True)

    q = migrate_engine.execute(revisions_table.select())
    for (id, _, text, _, _, _, title) in q:
        title = title and title.strip() or ''
        if len(title) < 5:
            continue
        if title.startswith('Re: '):
            continue
        new_text = ('**%(title)s**\n'
                    '\n'
                    '%(text)s') % {'title': title,
                                   'text': text}
        update_statement = revisions_table.update(
            revisions_table.c.id == id, {'text': new_text})
        migrate_engine.execute(update_statement)

    revisions_table.c.title.drop()


def downgrade(migrate_engine):
    raise NotImplementedError()
