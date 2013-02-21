from datetime import datetime

from sqlalchemy import *
from migrate import *
import migrate.changeset

meta = MetaData()

delegateable_table = Table('delegateable', meta,
    Column('id', Integer, primary_key=True),
    Column('label', Unicode(255), nullable=False),
    Column('type', String(50)),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('access_time', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
    Column('delete_time', DateTime, nullable=True),
    Column('creator_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('instance_id', Integer, ForeignKey('instance.id'), nullable=False)
    )


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    poll_table_old = Table('poll', meta,
        Column('id', Integer, primary_key=True),
        Column('begin_time', DateTime, default=datetime.utcnow),
        Column('end_time', DateTime, nullable=True),
        Column('begin_user_id', Integer, ForeignKey('user.id'), nullable=False),
        Column('proposal_id', Integer, ForeignKey('proposal.id'), nullable=False)   
        )
    
    proposal_table = Table('proposal', meta,
        Column('id', Integer, ForeignKey('delegateable.id'), primary_key=True),
        Column('comment_id', Integer, ForeignKey('comment.id'), nullable=True)
        )
    
    adopt_poll_id = Column('adopt_poll_id', Integer, ForeignKey('poll.id'), nullable=True)
    adopt_poll_id.create(proposal_table)
    
    action = Column('action', Unicode(50), nullable=True, default='adopt')
    subject = Column('subject', UnicodeText(), nullable=True)
    scope_id = Column('scope_id', Integer, ForeignKey('delegateable.id'), nullable=True)
    action.create(poll_table_old)
    subject.create(poll_table_old)
    scope_id.create(poll_table_old)
    poll_table_old.c.begin_user_id.alter(name="user_id")
    
    q = migrate_engine.execute(poll_table_old.select())
    for (id, _, _, _, proposal_id, _, _, _) in q:
        u = poll_table_old.update(id==poll_table_old.c.id, 
                                  {'scope_id': proposal_id,
                                   'subject': u"@[proposal:%s]" % proposal_id,
                                   'action': u'adopt'})
        migrate_engine.execute(u)
        q = proposal_table.update(proposal_table.c.id==proposal_id,
                                  {'adopt_poll_id': id})
        migrate_engine.execute(q)
    
    poll_table_old.c.proposal_id.drop()

def downgrade(migrate_engine):
    raise NotImplementedError() 

