import logging

import adhocracy.model as model

from decision import Decision
from delegation_node import DelegationNode
from state import State

from ..cache import memoize
from .. import queue


log = logging.getLogger(__name__)


def init_democracy(with_db=True):
    if with_db:
        try:
            for vote in model.Vote.all():
                handle_vote(vote)
        except Exception, e:
            log.exception("Cannot update tallies: %s" % e)
    
    queue.register(model.Vote, queue.INSERT, handle_vote)
    queue.register(model.Vote, queue.UPDATE, handle_vote)


def handle_vote(vote):
    #log.debug("Post-processing vote: %s" % vote)
    if model.Tally.find_by_vote(vote) is None:
        tally = model.Tally.create_from_vote(vote)
        model.meta.Session.commit()
        log.debug("Tallied %s: %s" % (vote.poll, tally))

