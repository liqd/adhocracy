import logging

from adhocracy.lib.democracy.decision import Decision
from adhocracy.lib.democracy.delegation_node import DelegationNode

from adhocracy.model import hooks, meta
from adhocracy.model import Delegation, Poll, Proposal, Tally, Vote


log = logging.getLogger(__name__)


def init_democracy(with_db=True):
    '''Register callback functions for  :class:`adhocracy.models.Vote`
    (:func:`handle_vote`) and :class:`adhocracy.models.Delegation`
    (:func:`update_tallies_on_delegation`)
    '''

    ## if with_db:
    ##     try:
    ##         for vote in Vote.all():
    ##             pass
    ##             #handle_vote(vote)
    ##     except Exception, e:
    ##         log.exception("Cannot update tallies: %s" % e)

    hooks.register_queue_callback(Vote, hooks.POSTINSERT, handle_vote)
    hooks.register_queue_callback(Vote, hooks.POSTUPDATE, handle_vote)
    hooks.register_queue_callback(Delegation, hooks.POSTINSERT,
                                  update_tallies_on_delegation)
    hooks.register_queue_callback(Delegation, hooks.POSTUPDATE,
                                  update_tallies_on_delegation)
    #check_adoptions()


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
        if not proposal.adopted and proposal.is_adopt_polling() \
            and proposal.adopt_poll.is_stable():
            log.info("Proposal %s is now ADOPTED. Thanks for playing." %
                     proposal.title)
            proposal.adopt()
            meta.Session.commit()
        # TODO check repeals


def update_tallies_on_delegation(delegation):
    for poll in Poll.within_scope(delegation.scope):
        tally = Tally.create_from_poll(poll)
        meta.Session.commit()
        log.debug("Tallied %s: %s" % (poll, tally))
