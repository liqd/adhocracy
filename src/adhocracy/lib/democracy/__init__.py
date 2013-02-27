import logging

from adhocracy.lib.democracy.decision import Decision
from adhocracy.lib.democracy.delegation_node import DelegationNode

from adhocracy.model import meta
from adhocracy.model import Delegation, Poll, Proposal, Tally, Vote


log = logging.getLogger(__name__)


def init_democracy():
    '''Register callback functions for  :class:`adhocracy.models.Vote`
    (:func:`handle_vote`) and :class:`adhocracy.models.Delegation`
    (:func:`update_delegation`)
    '''
    from adhocracy.lib.queue import LISTENERS
    from adhocracy.model.update import INSERT, UPDATE
    LISTENERS[(Vote, INSERT)].append(handle_vote)
    LISTENERS[(Vote, UPDATE)].append(handle_vote)
    LISTENERS[(Delegation, INSERT)].append(update_delegation)
    LISTENERS[(Delegation, UPDATE)].append(update_delegation)


def handle_vote(vote):
    #log.debug("Post-processing vote: %s" % vote)
    if Tally.find_by_vote(vote) is None:
        tally = Tally.create_from_vote(vote)
        meta.Session.commit()
        log.debug("Tallied %s: %s" % (vote.poll, tally))


def check_adoptions():
    log.debug("Checking proposals for successful adoption...")
    for proposal in Proposal.all():
        # check adoptions:
        if (not proposal.adopted and proposal.is_adopt_polling()
                and proposal.adopt_poll.is_stable()):
            log.info("Proposal %s is now ADOPTED. Thanks for playing." %
                     proposal.title)
            proposal.adopt()
            meta.Session.commit()
        # TODO check repeals


def update_delegation(delegation):
    for poll in Poll.within_scope(delegation.scope):
        tally = Tally.create_from_poll(poll)
        meta.Session.commit()
        log.debug("Tallied %s: %s" % (poll, tally))
