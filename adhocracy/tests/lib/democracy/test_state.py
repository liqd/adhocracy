# REFACT: somehow get this down to one import for all unit test stuff
from adhocracy.tests import TestController
from adhocracy.tests.testtools import tt_make_proposal, tt_make_user

from adhocracy.lib.democracy import State, Decision
from adhocracy.model import Vote


class TestState(TestController):
    pass
    # def test_stats(self):
    #     proposal = tt_make_proposal(voting=True)
    #     poll = proposal.poll
    #     proposal.creator.vote_for_proposal(proposal, Vote.YES)
    #     state = State(proposal, poll)
    #     assert poll.num_affirm == 1
    #     assert poll.rel_for == 1.0
    #     Decision(tt_make_user(), p).make(Vote.NO)
    #     poll = Poll(proposal, proposal.creator)
    #     assert len(poll.voters) == 2
    #     assert poll.num_dissent == 1
    #     assert poll.rel_for == 1.0/2.0
    #     Decision(tt_make_user(), p).make(Vote.ABSTAIN)
    #     poll = Poll(proposal)
    #     assert len(poll.voters) == 3
    #     assert poll.num_abstain == 1
