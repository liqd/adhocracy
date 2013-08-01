from paste.deploy.converters import asbool

from adhocracy.lib.cache.util import memoize


def calc_votedetail(instance, poll):
    from adhocracy.model import User, Badge
    from adhocracy.lib.democracy import tally as _tally
    res = []
    for badge in instance.votedetail_userbadges:
        uf = lambda q: q.join(User.badges).filter(Badge.id == badge.id)
        tally = _tally.make_from_poll(_tally.SimpleTally, poll, user_filter=uf)
        res.append((badge, tally))
    return res


@memoize('votedetail')
def calc_votedetail_dict(instance, poll, badge_title_only=False):
    badge_value = lambda b: b.title if badge_title_only else b.to_dict()
    return [{'badge': badge_value(b), 'tally': t.to_dict()}
            for b, t in calc_votedetail(instance, poll)]


def is_enabled():
    from pylons import config
    return asbool(config.get('adhocracy.enable_votedetail', 'false'))
