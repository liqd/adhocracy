from adhocracy.model import Poll, Vote

from adhocracy.tests import TestController
from adhocracy.tests.testtools import tt_make_proposal


class TestPoll(TestController):

    def test_begin_end(self):
        proposal = tt_make_proposal(voting=False)
        poll = Poll.create(proposal, proposal.creator, Poll.ADOPT)
        poll.end()
        self.assertTrue(poll.has_ended())

    def test_poll(self):
        proposal = tt_make_proposal(voting=True)
        poll = proposal.polls[0]
        self.assertEqual(0, len(list(poll.votes)))
        proposal.creator.vote_on_poll(poll, Vote.YES)[0]
        self.assertEqual(len(poll.votes), 1)


# REFACT: enable the proposal to be able to have many polls in parallel
