# open with bin/adhocpy

"""Move all contents of on instance into another one."""

import os
import sys
from argparse import ArgumentParser

from paste.deploy import appconfig
import pylons
from pylons.i18n.translation import _get_translator

from adhocracy.config.environment import load_environment
from adhocracy import model


def load_config(filename):
    conf = appconfig('config:' + os.path.abspath(filename) + '#content')
    config = load_environment(conf.global_conf, conf.local_conf)
    pylons.config.update(config)
    translator = _get_translator(pylons.config.get('lang'))
    pylons.translator._push_object(translator)


def parse_args():
    parser = ArgumentParser(description=__doc__)

    parser.add_argument('--conf_file', '-c', help=u'configuration to use')
    parser.add_argument('src_instance',
                        help=u'move objects from this instance')
    parser.add_argument('trgt_instance', help=u'move objects to this instance')

    return parser.parse_args()


def merge(i1, i2):
    # merge objects
    tables = [
        model.badge_table,
        model.delegateable_table,
        model.event_table,
        model.message_table,
        model.milestone_table,
        model.votedetail_table,
    ]
    for t in tables:
        print(u"merging %s" % t.name)
        stmt = t.update()\
            .where(t.c.instance_id == i1.id)\
            .values(instance_id=i2.id)
        model.meta.Session.execute(stmt)

    # merge members
    print(u"merging membership")
    memberships = model.Membership.all_q()\
        .filter(model.Membership.instance == i1).all()
    for m in memberships:
        if m.user.instance_membership(i2) is None:
            m.instance = i2
            model.meta.Session.add(m)

    model.meta.Session.commit()


def main():
    args = parse_args()
    load_config(args.conf_file)

    i1 = model.Instance.find(args.src_instance)
    if i1 is None:
        print(u"Could not find source instance %s" % args.src_instance)
        return 1

    i2 = model.Instance.find(args.trgt_instance)
    if i2 is None:
        print(u"Could not find target instance %s" % args.trgt_instance)
        return 1

    return merge(i1, i2)

if __name__ == '__main__':
    sys.exit(main())
