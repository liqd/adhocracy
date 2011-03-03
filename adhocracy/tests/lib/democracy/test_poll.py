from nose.tools import assert_equals, assert_true

from adhocracy.model import Poll, Vote

from adhocracy.tests import TestController
from adhocracy.tests.testtools import tt_make_proposal


class TestPoll(TestController):

    def test_begin_end(self):
        proposal = tt_make_proposal(voting=False)
        poll = Poll.create(proposal, proposal.creator, Poll.ADOPT)
        poll.end()
        assert_true(poll.has_ended())

    def test_poll(self):
        proposal = tt_make_proposal(voting=True)
        poll = proposal.polls[0]
        assert_equals(0, len(list(poll.votes)))
        proposal.creator.vote_on_poll(poll, Vote.YES)[0]
        assert_equals(len(poll.votes), 1)


# REFACT: enable the proposal to be able to have many polls in parallel
