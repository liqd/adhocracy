import logging

from adhocracy.lib.democracy.decision import Decision
from adhocracy.lib.democracy.delegation_node import DelegationNode

from adhocracy.model import hooks, meta
from adhocracy.model import Delegation, Poll, Proposal, Tally, Vote


log = logging.getLogger(__name__)


def init_democracy(with_db=True):
    '''Patch _post_insert() and _post_update() functions into
    :class:`adhocracy.models.Vote` and :class:`adhocracy.models.Delegation`
    The patched in function will update the tally of votes.
    It will be called by :class:`adhocracy.model.hooks.HookExtension`
    before and after changed models are commited to the database.

    ..Warning::

    The patched in functions overwrite patches from
    :func:`adhocracy.model.hooks.init_queue_hooks`
    '''

    if with_db:
        try:
            for vote in Vote.all():
                pass
                #handle_vote(vote)
        except Exception, e:
            log.exception("Cannot update tallies: %s" % e)

    log.debug('PATCHING model classes with pre_* and post_* functions '
              'to update the tallies of votes to be used in pre/post '
              'commit hooks. patched: \n%s\n%s\n'
              'WARNING: this overwrites other patches' % (Delegation, Vote))

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
