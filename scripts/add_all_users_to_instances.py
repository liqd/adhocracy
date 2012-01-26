#!/usr/bin/env python
"""Add all users into the instances given on the command line.
"""
import os
import sys
from argparse import ArgumentParser

from paste.deploy import appconfig
from adhocracy.config.environment import load_environment
from adhocracy import model


def load_config(filename):
    conf = appconfig('config:' + os.path.abspath(filename) + '#content')
    load_environment(conf.global_conf, conf.local_conf)


def parse_args():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("conf_file", help="configuration to use")
    parser.add_argument("instance_keys", metavar='instance', nargs='+',
                        help=("Instance key(s). If ALL is given, the "
                              "users will be added to all visible instances."))
    return parser.parse_args()


def main():
    args = parse_args()
    load_config(args.conf_file)
    session = model.meta.Session

    num_added = {}
    keys_added = {}

    def increment(dict_, key):
        num = dict_.get(key, 0)
        num += 1
        dict_[key] = num

    # filter the instances we have to add
    instance_keys = args.instance_keys
    instances = model.Instance.all()
    if not 'ALL' in instance_keys:
        instances = [instance for instance in instances if instance.key
                     in instance_keys]

    num_instances = len(instances)
    users = model.User.all()
    num_users = len(users)
    total_added = 0

    print "\n***Adding users***\n"
    for user in users:
        user_status = user.user_name + ': '
        added = 0
        for instance in set(instances) - set(user.instances):
            increment(keys_added, instance.key)
            user_status += instance.key + ' '
            added += 1
            total_added += 1
            membership = model.Membership(user, instance,
                                          instance.default_group)
            session.add(membership)
            if (total_added % 2) == 0:
                session.commit()
        if added:
            print "%s (%s)" % (user_status, added)
        increment(num_added, added)
    session.commit()

    print "\n***Statistics***"
    print "Instances:", num_instances
    print "Users:", num_users

    print "\n**Instances added per user**\n"
    added = 0
    for (key, count) in sorted(num_added.items()):
        added += key * count
        print "%s membership added for %s users" % (key, count)
    print ''
    print "Mean number of memberships added per user: %s" % (float(added) /
                                                             float(num_users))

    print "\n**Users added per group**\n"
    for key in sorted(keys_added.keys()):
        print "%s: %s" % (key, (float(keys_added[key]) / float(num_users)))


if __name__ == '__main__':
    sys.exit(main())
