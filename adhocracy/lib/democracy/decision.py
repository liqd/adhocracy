from datetime import datetime, timedelta
import logging

from sqlalchemy import and_, or_
from sqlalchemy.orm import eagerload

from ..cache import memoize
import adhocracy.model as model
from adhocracy.model import Proposal, Vote, Poll, User

from delegation_node import DelegationNode

log = logging.getLogger(__name__)

class DecisionException(Exception):
    """ A general exception for ``Decision`` errors """
    pass

class Decision(object):
    """
    A decision describes the current or past opinion that a user has 
    expressed on a given poll. This includes opinions that were determined
    by an agent as a result of delegation. 
    """
    
    def __init__(self, user, poll, at_time=None, votes=None):
        self.user = user
        self.poll = poll
        self.at_time = at_time
        self.node = DelegationNode(user, poll.proposal)
        self.votes = votes
        if not votes: 
            self.reload()
    
    def reload(self):
        """ 
        Load all votes by the user regarding the poll. 
        """
        q = model.meta.Session.query(Vote)
        q = q.filter(Vote.user_id == self.user.id)
        q = q.filter(Vote.poll_id == self.poll.id)
        q = q.options(eagerload(Vote.delegation))
        if self.at_time:
            q = q.filter(Vote.create_time<=self.at_time)
        q = q.order_by(Vote.id.desc())
        self.votes = q.all()
        return self
    
    def _relevant_votes(self):
        """ 
        Currently relevant votes for the polling interval. 
        
        **WARNING**: A non-empty list of relevant votes does not always 
        mean a decision was made. This is not true, for example, when multiple
        delegates match a proposal and their opinions differ.
        
        :returns: List of ``Vote``
        """
        relevant = {}
        for vote in self.votes:
            if not vote.delegation:
                return [vote]
            if relevant.get(vote.delegation, vote).create_time <= vote.create_time:
                relevant[vote.delegation] = vote
        use_keys = self.node.filter_less_specific_delegations(relevant.keys())
        return [v for k, v in relevant.items() if k in use_keys]
        
    relevant_votes = property(_relevant_votes)
    
    def _create_time(self):
        """
        Utility property to see when this decision became effective. Equals 
        the latest relevant vote creation date. 
        
        :returns: datetime
        """
        return max(map(lambda v: v.create_time, self.relevant_votes))
    
    create_time = property(_create_time)
    
    def _delegations(self):
        """
        The set of delegations which have determined this decision, as per 
        ``relevant_votes``. 
        
        :returns: list of ``Delegation``
        """
        return filter(lambda d: d is not None, 
                      list(set(map(lambda v: v.delegation, 
                                   self.relevant_votes))))
    
    delegations = property(_delegations)
    
    def _result(self):
        """ 
        The result is an ``orientation`` and reflects the ``User``'s current 
        decision on the ``Proposal``. Values match those in ``Vote``. Given multiple 
        delegates who have voted on the proposal, the current approach is to check 
        for an unanimous decision and to discard all other constellations. Another
        approach would be to require only a certain majority of agents to support an 
        opinion, thus creating an inner vote.  
        """ 
        relevant = self.relevant_votes
        orientations = set(map(lambda v: v.orientation, relevant))
        if len(relevant) and len(orientations) == 1:
            return orientations.pop()
        return None
    
    result = property(_result)
    
    # REFACT: this api is dangeous as it assumes but does not check that a poll is actually open for this proposal
    def make(self, orientation, _edge=None):
        """
        Make a decision on a given proposal, i.e. vote. Voting recursively propagates 
        through the delegation graph to all principals who have assigned voting 
        power to the ``User``. Each delegated vote will be marked as such by 
        saving the ``Delegation`` as a part of the ``Vote``.
        
        :param orientation: orientation of the vote, ``Vote.YES``, ``Vote.NO`` 
            or ``Vote.ABSTAIN``
        :returns: the ``Votes`` that has been cast
        """
        
        def propagating_vote(user, proposal, edge):
            vote = Vote(user, self.poll, orientation, delegation=edge)
            model.meta.Session.add(vote)
            log.debug("Decision was made: %s is voting '%s' on %s (via %s)" % (repr(user), 
                                                                orientation, repr(self.poll.proposal.id),
                                                                edge if edge else "self"))
            return vote
        
        votes = self.node.propagate(propagating_vote, _edge=_edge)
        model.meta.Session.commit()
        self.reload()
        return votes
    
    def is_decided(self):
        """
        Determine if a given decision was made by the user, i.e. if the user
        or one of his/her agents has voted on the proposal. 
        """
        return not self.result == None
    
    def is_self_decided(self):
        """
        Determine if a given decision was made by the user him-/herself. 
        This does not consider decisions determined by delegation.
        """
        
        relevant = self.relevant_votes
        return len(relevant) == 1 and relevant[0].delegation == None
    
    def __repr__(self):
        return "<Decision(%s,%s)>" % (self.user.user_name, self.poll.id)
    
    def without_vote(self, vote):
        """
        Return the same decision given that a certain vote had not been 
        cast. 
        """
        if not vote in self.relevant_votes:
            return self
        else:
            votes = [v for v in self.votes if v != vote]
            return Decision(self.user, self.poll, 
                            at_time=self.at_time, votes=votes)   
    
    def to_dict(self):
        d = dict(user=self.user.user_name,
                 poll=self.poll.id,
                 decided=self.is_decided(),
                 self_decided=self.is_self_decided())
        if self.is_decided():
            d['result'] = self.result
        d['delegations'] = map(lambda d: d.id, self.delegations)
        return d        
    
    @classmethod
    def for_user(cls, user, instance, at_time=None):  # FUUUBARD 
        """
        Give a list of all decisions the user made within an instance context.
        
        :param user: The user for which to list ``Decisions``
        :param instance: an ``Instance`` context. 
        """
        query = model.meta.Session.query(Poll)
        query = query.distinct().join(Vote)
        query = query.join(Proposal)
        query = query.filter(Proposal.instance==instance)
        query = query.filter(Vote.user==user)
        query = query.options(eagerload(Poll.proposal))
        for poll in query:
            if not instance or poll.proposal.instance == instance:
                yield cls(user, poll, at_time=at_time)
    
    @classmethod
    def for_poll(cls, poll, at_time=None):
        """
        Get all decisions that have been made on a poll.
        
        :param poll: The poll on which to get decisions. 
        """
        query = model.meta.Session.query(User)
        query = query.distinct().join(Vote)
        query = query.filter(Vote.poll_id==poll.id)
        if at_time:
            query = query.filter(Vote.create_time<=at_time)
        return [Decision(u, poll, at_time=at_time) for u in query]
    
    @classmethod
    def average_decisions(cls, instance):
        """
        The average number of decisions that a ``Poll`` in the given instance 
        has. For each proposal, this only includes the current poll in order to 
        not accumulate too much historic data.
        
        :param instance: the ``Instance`` for which to calculate the average.   
        """
        @memoize('average_decisions', 84600)
        def avg_decisions(instance):
            query = model.meta.Session.query(Poll)
            query = query.join(Proposal).filter(Proposal.instance_id==instance.id)
            query = query.filter(Poll.end_time==None)
            decisions = []
            for poll in query:
                if not poll.end_time: 
                    # only consider current polls to allow for drops 
                    # in participation
                    decisions.append(len(Decision.for_poll(poll)))
            return sum(decisions)/float(max(1,len(decisions)))
        return avg_decisions(instance)
    
    @classmethod
    def replay_decisions(cls, delegation):
        """
        For a new delegation, have the principal reproduce all of the agents
        past decisions within the delegation scope. This process is not perfect, 
        since not the full voting history is reproduced, but only the latest 
        interim result. The resulting decisions should be the same, though.
        
        :param delegation: The delegation that is newly created. 
        """
        votes = []
        for decision in cls.for_user(delegation.agent, delegation.scope.instance, 
                                     at_time=delegation.create_time):
            #log.debug("RP: Decision %s" % decision)
            if delegation.is_match(decision.poll.proposal):
                if not decision.poll.end_time: 
                    log.debug("RP: Making %s" % decision)
                    principal_dec = Decision(delegation.principal, decision.poll)
                    votes += principal_dec.make(decision.result, _edge=delegation)
        return votes
    
    

