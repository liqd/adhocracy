from sqlalchemy import MetaData
from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy import Boolean, Integer, Unicode

metadata = MetaData()


def upgrade(migrate_engine):
    metadata.bind = migrate_engine

    instance_table = Table('instance', metadata, autoload=True)
    allow_propose_changes = Column('allow_propose_changes', Boolean,
                                   default=True)
    allow_propose_changes.create(instance_table)

    page_table = Table('page', metadata, autoload=True)

    page_sectionpage = Column('sectionpage', Boolean, default=False)
    page_allow_comment = Column('allow_comment', Boolean, default=True)
    page_allow_selection = Column('allow_selection', Boolean, default=True)
    page_always_show_original = Column('always_show_original', Boolean,
                                       default=True)

    page_sectionpage.create(page_table)
    page_allow_comment.create(page_table)
    page_allow_selection.create(page_table)
    page_always_show_original.create(page_table)

    migrate_engine.execute(update)


def downgrade(migrate_engine):
    raise NotImplementedError()
