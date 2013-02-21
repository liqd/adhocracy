from datetime import datetime
from pprint import pprint 

from sqlalchemy import *
from migrate import *
import migrate.changeset

import adhocracy.lib.text as text

meta = MetaData()

category_graph = Table('category_graph', meta,
    Column('parent_id', Integer, ForeignKey('delegateable.id')),
    Column('child_id', Integer, ForeignKey('delegateable.id'))
    )

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
    
poll_table = Table('poll', meta,
    Column('id', Integer, primary_key=True),
    Column('begin_time', DateTime, default=datetime.utcnow),
    Column('end_time', DateTime, nullable=True),
    Column('user_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('action', Unicode(50), nullable=False),
    Column('subject', UnicodeText(), nullable=False),
    Column('scope_id', Integer, ForeignKey('delegateable.id'), nullable=False)
    )
    
comment_table = Table('comment', meta,                  
    Column('id', Integer, primary_key=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('delete_time', DateTime, default=None, nullable=True),
    Column('creator_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('topic_id', Integer, ForeignKey('delegateable.id'), nullable=False),
    Column('canonical', Boolean, default=False),
    Column('wiki', Boolean, default=False),
    Column('reply_id', Integer, ForeignKey('comment.id'), nullable=True),
    Column('poll_id', Integer, ForeignKey('poll.id'), nullable=True)
    )

revision_table = Table('revision', meta,
    Column('id', Integer, primary_key=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('text', UnicodeText(), nullable=False),
    Column('sentiment', Integer, default=0),
    Column('user_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('comment_id', Integer, ForeignKey('comment.id'), nullable=False)
    )

tally_table = Table('tally', meta,
    Column('id', Integer, primary_key=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('poll_id', Integer, ForeignKey('poll.id'), nullable=False),
    Column('vote_id', Integer, ForeignKey('vote.id'), nullable=True),
    Column('num_for', Integer, nullable=True),
    Column('num_against', Integer, nullable=True),
    Column('num_abstain', Integer, nullable=True)
    )

vote_table = Table('vote', meta, 
    Column('id', Integer, primary_key=True),
    Column('orientation', Integer, nullable=False),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('user_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('poll_id', Integer, ForeignKey('poll.id'), nullable=False),
    Column('delegation_id', Integer, ForeignKey('delegation.id'), nullable=True)
    )
    
page_table = Table('page', meta,                      
    Column('id', Integer, ForeignKey('delegateable.id'), primary_key=True),
    Column('part', Unicode)
    )
    
text_table = Table('text', meta,                      
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

def upgrade(migrate_engine):
    meta.bind = migrate_engine
    proposal_table = Table('proposal', meta,
        Column('id', Integer, ForeignKey('delegateable.id'), primary_key=True),
        Column('comment_id', Integer, ForeignKey('comment.id'), nullable=True),
        Column('adopt_poll_id', Integer, ForeignKey('poll.id'), nullable=True),
        Column('rate_poll_id', Integer, ForeignKey('poll.id'), nullable=True),
        Column('adopted', Boolean, default=False)
        )
    
    description = Column('description_id', Integer, nullable=True) # ForeignKey('page.id'), 
    if migrate_engine.url.drivername == "sqlite":
        description = Column('description_id', Integer, nullable=True)
    description.create(proposal_table)
    
    q1 = migrate_engine.execute(proposal_table.select())
    for (prop_id, comment_id, _, _, _, _) in q1:
        instance_id = None
        label = None
        ctime = None
        dtime = None
        q4 = migrate_engine.execute(delegateable_table.select(' delegateable.id = %d ' % prop_id))
        for (_, _label, _type, _ctime, _dtime, _, _, _instance_id) in q4:
            instance_id = _instance_id
            label = _label
            ctime = _ctime
            dtime = _dtime
        
        if comment_id is None: 
            continue
        
        q2 = migrate_engine.execute(comment_table.select(' comment.id = %d ' % comment_id))
        for (_, _, _, creator_id, topic_id, _, _, _, poll_id) in q2:
            migrate_engine.execute(vote_table.delete(vote_table.c.poll_id==poll_id))
            migrate_engine.execute(tally_table.delete(tally_table.c.poll_id==poll_id))
            migrate_engine.execute(poll_table.delete(poll_table.c.id==poll_id))
        
            
            q3 = delegateable_table.insert(values={'label': text.title2alias(label), 
                                          'type': u'page',
                                          'create_time': ctime,
                                          'delete_time': None,
                                          'creator_id': creator_id,
                                          'instance_id': instance_id})
            r = migrate_engine.execute(q3)
            page_id = r.last_inserted_ids()[-1]
            
            q5 = page_table.insert(values={'id': page_id, 
                                           'function': u'description'})
            r = migrate_engine.execute(q5)
            
            q10 = category_graph.insert(values={'parent_id': page_id, 
                                               'child_id': prop_id})
            r = migrate_engine.execute(q10)
            
            u4 = proposal_table.update(proposal_table.c.id==prop_id, values={
                'description_id': page_id,
                'comment_id': None
                })
            migrate_engine.execute(u4)
            
            q6 = migrate_engine.execute(revision_table.select(' revision.comment_id = %d ' % comment_id))
            last_id = None
            for (r_id, t_ctime, t_text, _, t_creator_id, _) in q6:
                q7 = text_table.insert(values={'title': label, 
                                              'text': t_text,
                                              'create_time': t_ctime,
                                              'delete_time': None,
                                              'user_id': t_creator_id,
                                              'page_id': page_id,
                                              'variant': u'HEAD',
                                              'parent_id': last_id})
                r = migrate_engine.execute(q7)
                last_id = r.last_inserted_ids()[-1]
                
            def move_comment(data):
                (c_id, c_ctime, c_dtime, c_user_id, c_topic_id, c_can, c_wiki, c_reply_id, c_poll_id) = data
                
                if c_reply_id == comment_id:
                    u1 = comment_table.update(comment_table.c.id==c_id, values={
                        'reply_id': None
                        })
                    migrate_engine.execute(u1)
                
                u2 = comment_table.update(comment_table.c.id==c_id, values={
                    'topic_id': page_id
                    })
                migrate_engine.execute(u2)
                
                u3 = poll_table.update(poll_table.c.id==c_poll_id, values={
                    'scope_id': page_id
                    })
                migrate_engine.execute(u3)
                migrate_engine.execute(tally_table.delete(tally_table.c.poll_id==c_poll_id))
                
                q8 = migrate_engine.execute(comment_table.select(' comment.reply_id = %d ' % c_id))
                for d in q8: 
                    move_comment(d)
                    
            q9 = migrate_engine.execute(comment_table.select(' comment.reply_id = %d ' % comment_id))
            for d in q9: 
                move_comment(d)
            
            migrate_engine.execute(revision_table.delete(revision_table.c.comment_id==comment_id))   
            migrate_engine.execute(comment_table.delete(comment_table.c.id==comment_id))   
            
            
    #proposal_table.c.comment_id.drop()

def downgrade(migrate_engine):
    raise NotImplementedError()

