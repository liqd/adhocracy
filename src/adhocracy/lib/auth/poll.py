from paste.deploy.converters import asbool
from pylons import config, tmpl_context as c
import user


def index(check):
    check.perm('poll.show')


def show(check, p):
    check.perm('poll.show')
    check.other('poll_has_ended', p.has_ended())
    hide_cfg = asbool(config.get('adhocracy.hide_individual_votes', 'false'))
    check.other('hide_individual_votes', hide_cfg)


def create(check):
    check.valid_email()
    check.perm('poll.create')


def edit(check, p):
    check.valid_email()
    check.other('polls_can_not_be_edited', True)


def delete(check, p):
    check.valid_email()
    check.perm('poll.delete')
    show(check, p)
    check.other('poll_can_not_end', not p.can_end())


def vote(check, p):
    check.valid_email()
    check.other('poll_has_ended', p.has_ended())
    check.other('instance_frozen', c.instance.frozen)

    check.other('select_poll_not_mutable',
                (p.action == p.SELECT and p.selection and
                 not p.selection.proposal.is_mutable()))
    user.vote(check)
