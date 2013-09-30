from sqlalchemy import MetaData
from sqlalchemy import Column, Table
from sqlalchemy import Boolean

metadata = MetaData()


def upgrade(migrate_engine):
    metadata.bind = migrate_engine

    instance_table = Table('instance', metadata, autoload=True)
    allow_propose_changes = Column('allow_propose_changes', Boolean,
                                   default=True)
    allow_propose_changes.create(instance_table)

    proposal_table = Table('proposal', metadata, autoload=True)
    is_amendment = Column('is_amendment', Boolean,
                          default=False)
    is_amendment.create(proposal_table)

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


def downgrade(migrate_engine):
    raise NotImplementedError()
