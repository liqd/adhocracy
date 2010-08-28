import logging

import adhocracy.model as model

from decision import Decision
from delegation_node import DelegationNode

from adhocracy.model import hooks


log = logging.getLogger(__name__)


def init_democracy(with_db=True):
    if with_db:
        try:
            for vote in model.Vote.all():
                pass
                #handle_vote(vote)
        except Exception, e:
            log.exception("Cannot update tallies: %s" % e)
    
    hooks.register_queue_callback(model.Vote, hooks.POSTINSERT, handle_vote)
    hooks.register_queue_callback(model.Vote, hooks.POSTUPDATE, handle_vote)
    hooks.register_queue_callback(model.Delegation, hooks.POSTINSERT, update_tallies_on_delegation)
    hooks.register_queue_callback(model.Delegation, hooks.POSTUPDATE, update_tallies_on_delegation)
    #check_adoptions()


def handle_vote(vote):
    #log.debug("Post-processing vote: %s" % vote)
    if model.Tally.find_by_vote(vote) is None:
        tally = model.Tally.create_from_vote(vote)
        model.meta.Session.commit()
        log.debug("Tallied %s: %s" % (vote.poll, tally))


def check_adoptions():
    log.debug("Checking proposals for successful adoption...")
    for proposal in model.Proposal.all():
        # check adoptions:
        if not proposal.adopted and proposal.is_adopt_polling() \
            and proposal.adopt_poll.is_stable():
            log.info("Proposal %s is now ADOPTED. Thanks for playing." % proposal.title)
            proposal.adopt()
            model.meta.Session.commit()
        # TODO check repeals
    

def update_tallies_on_delegation(delegation):
    for poll in model.Poll.within_scope(delegation.scope):
        tally = model.Tally.create_from_poll(poll)
        model.meta.Session.commit()
        log.debug("Tallied %s: %s" % (poll, tally))
