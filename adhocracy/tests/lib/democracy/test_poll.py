from adhocracy.model import Poll, Vote

from adhocracy.tests import TestController
from adhocracy.tests.testtools import tt_make_proposal, tt_make_user


class TestPoll(TestController):

    def test_begin_end(self):
        proposal = tt_make_proposal(voting=False)
        poll = Poll.create(proposal, proposal.creator, Poll.ADOPT)
        poll.end()
        self.assertTrue(poll.has_ended())

    def test_vote_by_creator(self):
        from adhocracy.lib.democracy import Decision
        proposal = tt_make_proposal(voting=True)
        poll = proposal.polls[0]
        self.assertEqual(0, len(list(poll.votes)))
        decision = Decision(proposal.creator, poll)
        votes = decision.make(Vote.YES)
        self.assertEqual(len(votes), 1)
        self.assertEqual(len(decision.votes), 1)
        self.assertEqual(votes[0].orientation, Vote.YES)
        self.assertEqual(votes[0].user, proposal.creator)

    def test_second_identical_vote(self):
        from adhocracy.lib.democracy import Decision
        proposal = tt_make_proposal(voting=True)
        poll = proposal.polls[0]
        self.assertEqual(0, len(list(poll.votes)))
        decision = Decision(proposal.creator, poll)
        votes = decision.make(Vote.YES)
        self.assertEqual(len(votes), 1)
        self.assertEqual(len(decision.votes), 1)
        self.assertEqual(len(poll.votes), 1)

        # a second, identical vote by the same user
        decision = Decision(proposal.creator, poll)
        votes = decision.make(Vote.YES)
        self.assertEqual(len(votes), 1)
        self.assertEqual(len(decision.votes), 2)
        self.assertEqual(len(poll.votes), 2)

    def test_second_revised_vote(self):
        from adhocracy.lib.democracy import Decision
        proposal = tt_make_proposal(voting=True)
        poll = proposal.polls[0]
        self.assertEqual(0, len(list(poll.votes)))
        decision = Decision(proposal.creator, poll)
        votes = decision.make(Vote.YES)
        self.assertEqual(len(votes), 1)
        self.assertEqual(len(decision.votes), 1)
        self.assertEqual(len(poll.votes), 1)
        self.assertEqual(votes[0].orientation, Vote.YES)

        # a second, revised vote by the same user
        decision = Decision(proposal.creator, poll)
        votes = decision.make(Vote.NO)
        self.assertEqual(len(decision.votes), 2)
        self.assertEqual(len(poll.votes), 2)
        self.assertEqual(votes[0].orientation, Vote.NO)

    def test_vote_by_other_user(self):
        from adhocracy.lib.democracy import Decision
        proposal = tt_make_proposal(voting=True)
        poll = proposal.polls[0]
        self.assertEqual(0, len(list(poll.votes)))

        # make a new user and let him vote
        new_user = tt_make_user()
        decision = Decision(new_user, poll)
        votes = decision.make(Vote.YES)
        self.assertEqual(len(votes), 1)
        self.assertEqual(len(decision.votes), 1)
        self.assertEqual(len(poll.votes), 1)
        self.assertEqual(votes[0].orientation, Vote.YES)

# REFACT: enable the proposal to be able to have many polls in parallel
