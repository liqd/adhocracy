from sqlalchemy import Table, Column
from sqlalchemy import Integer, ForeignKey
from adhocracy.model import meta
from paste.deploy.converters import asbool

votedetail_table = Table(
    'votedetail', meta.data,
    Column('instance_id', Integer,
           ForeignKey('instance.id', ondelete='CASCADE')),
    Column('badge_id', Integer,
           ForeignKey('badge.id', ondelete='CASCADE')),
)


def calc_votedetail(instance, poll):
    from adhocracy.model import User, Badge
    from adhocracy.lib.democracy import tally as _tally
    res = []
    for badge in instance.votedetail_userbadges:
        uf = lambda q: q.join(User.badges).filter(Badge.id == badge.id)
        tally = _tally.make_from_poll(_tally.SimpleTally, poll, user_filter=uf)
        res.append((badge, tally))
    return res


def calc_votedetail_dict(instance, poll):
    return [{'badge': b.to_dict(), 'tally': t.to_dict()}
            for b, t in calc_votedetail(instance, poll)]


def is_enabled():
    from pylons import config
    return asbool(config.get('adhocracy.enable_votedetail', 'false'))
