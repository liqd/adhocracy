from adhocracy.lib.democracy import Decision
from adhocracy.model import Poll, Vote

from adhocracy.tests import TestController
from adhocracy.tests.testtools import tt_get_instance
from adhocracy.tests.testtools import tt_make_proposal, tt_make_user


class TestDecisionWithoutDelegation(TestController):

    def setUp(self):
        super(TestDecisionWithoutDelegation, self).setUp()
        self.proposal = tt_make_proposal(voting=True)
        self.poll = Poll.create(self.proposal, self.proposal.creator,
                                Poll.ADOPT)
        self.decision = Decision(self.proposal.creator, self.poll)

    def test_new_decisions_have_no_votes(self):
        self.assertEqual(len(self.decision.votes), 0)
        self.assertEqual(len(self.decision.relevant_votes), 0)
        self.assertEqual(self.decision.result, None,
                         "Not voted yet == not recorded for quorum")
        # TODO: this quorum thing needs additional tests

    def test_new_decisions_are_not_decided(self):
        self.assertFalse(self.decision.is_decided())
        self.assertFalse(self.decision.is_self_decided())

    def test_can_vote_directly(self):
        self.decision.make(Vote.YES)
        self.assertEqual(self.decision.result, Vote.YES)

    def test_decision_with_a_vote_is_decided(self):
        self.decision.make(Vote.YES)
        self.assertTrue(self.decision.is_decided())
        self.assertTrue(self.decision.is_self_decided())

    def test_can_override_previous_choice(self):
        self.decision.make(Vote.YES)
        self.assertEqual(self.decision.result, Vote.YES)
        self.decision.make(Vote.ABSTAIN)
        self.assertEqual(self.decision.result, Vote.ABSTAIN)
        self.decision.make(Vote.NO)
        self.assertEqual(self.decision.result, Vote.NO)

    def test_direct_votes_always_have_only_one_relevant_vote(self):
        self.decision.make(Vote.YES)
        self.decision.make(Vote.NO)
        self.decision.make(Vote.ABSTAIN)
        self.assertEqual(len(self.decision.relevant_votes), 1)

    # History access

    def test_multiple_votes_for_one_decision_are_recorded_for_posterity(self):
        self.decision.make(Vote.YES)
        self.decision.make(Vote.YES)
        self.assertEqual(len(self.decision.votes), 2)

    def test_old_decisions_can_be_retrieved(self):
        self.decision.make(Vote.YES)
        self.decision.make(Vote.YES)
        self.decision.make(Vote.NO)
        # votes are FIFO
        self.assertEqual(self.decision.votes[0].orientation, Vote.NO)
        self.assertEqual(self.decision.votes[1].orientation, Vote.YES)
        self.assertEqual(self.decision.votes[2].orientation, Vote.YES)


class TestDecisionWithDelegation(TestController):

    def setUp(self):
        super(TestDecisionWithDelegation, self).setUp()
        self.me = tt_make_user(name='me')
        self.high_delegate = tt_make_user(name='high_delegate')
        self.low_delegate = tt_make_user(name='low_delegate')

        self.proposal = tt_make_proposal(creator=self.me, voting=True)
        self.poll = Poll.create(self.proposal, self.proposal.creator,
                                Poll.ADOPT)
        self.decision = Decision(self.me, self.poll)
        self.instance = tt_get_instance()

    def _do_delegate(self, from_user, delegatee, scope):
        from adhocracy.model.delegation import Delegation
        delegation = Delegation.create(from_user, delegatee, scope)
        return delegation

    def test_delegation_without_vote_is_no_vote(self):
        self._do_delegate(self.me, self.high_delegate, self.proposal)
        self.decision.reload()
        self.assertEqual(len(self.decision.votes), 0)
        self.assertFalse(self.decision.is_decided())
        self.assertEqual(self.decision.result, None)

    def test_can_do_general_delegate_to_other_user(self):
        self._do_delegate(self.me, self.high_delegate, self.proposal)
        Decision(self.high_delegate, self.poll).make(Vote.YES)
        self.assertEqual(self.decision.reload().result, Vote.YES)

    def test_delegation_can_decide_a_decision(self):
        self._do_delegate(self.me, self.high_delegate, self.proposal)
        Decision(self.high_delegate, self.poll).make(Vote.YES)
        self.decision.reload()
        self.assertTrue(self.decision.is_decided())

    def test_delegated_decisions_are_not_self_decided(self):
        self._do_delegate(self.me, self.high_delegate, self.proposal)
        Decision(self.high_delegate, self.poll).make(Vote.YES)
        self.decision.reload()
        self.assertFalse(self.decision.is_self_decided())

    def test_two_delegations_at_the_same_level_that_disagree_cancel_each_other(
            self):
        # This is meant as a safeguard: if I don't fully trust my delegates
        # I can delegate to n delegates, and my vote will only be autocast
        # if they all agree
        # If not, I need to decide myself
        self._do_delegate(self.me, self.high_delegate, self.proposal)
        self._do_delegate(self.me, self.low_delegate, self.proposal)
        Decision(self.high_delegate, self.poll).make(Vote.YES)
        Decision(self.low_delegate, self.poll).make(Vote.NO)
        self.assertEqual(self.decision.reload().result, None,
                         "needs to cast his own vote")

    def test_two_delegations_at_the_same_level_that_agree_reinforce_each_other(
            self):
        self._do_delegate(self.me, self.high_delegate, self.proposal)
        self._do_delegate(self.me, self.low_delegate, self.proposal)
        Decision(self.high_delegate, self.poll).make(Vote.YES)
        Decision(self.low_delegate, self.poll).make(Vote.YES)
        self.assertEqual(self.decision.reload().result, Vote.YES)

    def test_two_delegations_at_the_same_level_are_both_relevant_votes(self):
        self._do_delegate(self.me, self.high_delegate, self.proposal)
        self._do_delegate(self.me, self.low_delegate, self.proposal)
        Decision(self.high_delegate, self.poll).make(Vote.YES)
        Decision(self.low_delegate, self.poll).make(Vote.YES)
        self.assertEqual(len(self.decision.reload().relevant_votes), 2)

    def test_own_vote_overrides_delegations(self):
        self._do_delegate(self.me, self.high_delegate, self.proposal)
        Decision(self.high_delegate, self.poll).make(Vote.YES)
        self.decision.make(Vote.NO)
        self.assertEqual(self.decision.reload().result, Vote.NO)

    def test_delegation_is_recorded_as_just_another_vote(self):
        self._do_delegate(self.me, self.high_delegate, self.proposal)
        self.assertEqual(len(self.decision.reload().votes), 0)
        Decision(self.high_delegate, self.poll).make(Vote.YES)
        self.assertEqual(len(self.decision.reload().votes), 1)

    def test_delegation_is_transitive(self):
        self._do_delegate(self.me, self.low_delegate, self.proposal)
        self._do_delegate(self.low_delegate, self.high_delegate, self.proposal)
        Decision(self.high_delegate, self.poll).make(Vote.YES)
        self.assertEqual(self.decision.reload().result, Vote.YES)

    def test_delegation_is_transitive_across_delegation_levels(self):
        self._do_delegate(self.me, self.low_delegate, self.proposal)
        self._do_delegate(self.low_delegate, self.high_delegate, self.proposal)
        Decision(self.high_delegate, self.poll).make(Vote.YES)
        self.assertEqual(self.decision.reload().result, Vote.YES)


# TODO: can access history of delegation decisions
# TODO: test replay - this is currently in the decision -
# TODO: could go to the DelegationNode though
# TODO: can delegate on all levels
