from adhocracy import config
from adhocracy.lib.helpers import url as _url


def url(poll, **kwargs):
    return _url.build(poll.scope.instance, 'poll', poll.id, **kwargs)


def hide_individual_votes(poll):
    hide = config.get_bool('adhocracy.hide_individual_votes.%s'
                           % poll.scope.instance.key)
    if hide is None:
        hide = config.get_bool('adhocracy.hide_individual_votes')
    return hide
