# open with bin/adhocpy

"""manage user invitations"""

import os
import sys
from argparse import ArgumentParser

import formencode
from paste.deploy import appconfig
import pylons
from pylons.i18n.translation import _get_translator

from adhocracy.config.environment import load_environment
from adhocracy.model import meta, Instance, User, UserBadge, UserBadges

from adhocracy.lib.user_import import user_import
from adhocracy.forms.common import UsersCSV, ContainsEMailPlaceholders


def load_config(filename):
    conf = appconfig('config:' + os.path.abspath(filename) + '#content')
    config = load_environment(conf.global_conf, conf.local_conf)
    pylons.config.update(config)
    translator = _get_translator(pylons.config.get('lang'))
    pylons.translator._push_object(translator)


def parse_args():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('conf_file', help=u'configuration to use')
    parser.add_argument('-b', '--badge', default=u'invited', help=u'badge'
                        u' (title or id) which is used to mark invited users')
    parser.add_argument('-i', '--instance', default=None)
    subparsers = parser.add_subparsers()

    invite_parser = subparsers.add_parser('invite', help=u'invite new users'
                                          u' to adhocracy')
    invite_parser.add_argument('csv_file', help=u'csv files of users to add')
    invite_parser.add_argument('template', help=u'text file with mail body')
    invite_parser.add_argument('-s', '--subject',
                               default=u"Welcome to Adhocracy!",
                               help=u'email subject')
    invite_parser.set_defaults(action=u'invite')

    reinvite_parser = subparsers.add_parser(
        'reinvite', help=u'invite again all users who have not yet activated'
        u' their accounts')
    reinvite_parser.add_argument('template', help=u'text file with mail body')
    reinvite_parser.add_argument('-s', '--subject',
                                 default=u"Welcome to Adhocracy!",
                                 help=u'email subject')
    reinvite_parser.set_defaults(action=u'reinvite')

    revoke_parser = subparsers.add_parser(
        'revoke', help=u'revoke invitation for all users who have not'
                       u' activated their accounts after invitation')
    revoke_parser.set_defaults(action=u'revoke')

    uninvite_parser = subparsers.add_parser(
        'uninvite', help=u'remove "invited"-badge from given users')
    uninvite_parser.add_argument('users', metavar='user', nargs='+')
    uninvite_parser.add_argument(
        '-r', '--revoke', action='store_true', help=u'also revoke invitation'
        u' if not already activated')
    uninvite_parser.set_defaults(action=u'uninvite')

    return parser.parse_args()


def invited_users(invited_badge, instance=None, joined=None, activated=None):
    """get all invited users

    joined/activated may be one of the following:

    -   True  - return only those invited users who have joined the instance/
                activated their accounts
    -   False - return only those invited users who have not joined the
                instance/activated their accounts
    -   None  - return all invited users
    """
    if instance is None and joined is not None:
        raise Exception('instance must not be None if joined specified')
    if joined is True:
        q = User.all_q(instance=instance)
    else:
        q = User.all_q(instance=None)
    q = q.join(UserBadges, UserBadges.user_id == User.id) \
         .filter(UserBadges.badge_id == invited_badge.id)
    users = q.all()
    if joined is False:
        users = filter(lambda u: instance not in u.instances, users)
    if activated is not None:
        users = filter(lambda u: u.is_email_activated() == activated, users)
    return users


def revoke(user):
    if len(user.instances) == 0:
        user.delete()
        print(u"revoked invitation for user %s" % user.user_name)
    else:
        print(u"did not revoke invitation for user %s: is member in"
              u" other instances" % user.user_name)


def uninvite(user, invited_badge, revoke=False):
    if invited_badge in user.badges:
        user.badges.remove(invited_badge)
        print(u"uninvited user %s" % user.user_name)
        if revoke:
            revoke(user)
    else:
        print(u"%s was not invited" % user.user_name)


def valid_instance(name):
    instance = Instance.find(name)
    if instance is None:
        print(u"Invalid instance: %s" % name)
        sys.exit(1)
    else:
        return instance


def valid_userbadge(title, instance=None):
    invited_badge = UserBadge.find_by_instance(title, instance)
    if invited_badge is None:
        invited_badge = UserBadge.create(title, u'#000000', False,
                                         u'This user has been invited',
                                         instance=instance)
        print(u"Badge %r created" % invited_badge)
    return invited_badge


def valid_template(filename):
    template_file = open(filename)
    template_string = template_file.read().decode('utf-8')
    template_file.close()
    template_validator = ContainsEMailPlaceholders(not_empty=True)
    try:
        return template_validator.to_python(template_string)
    except formencode.Invalid as e:
        print u"Invalid template: %s" % unicode(e.msg).replace('<br />', '\n')
        sys.exit(1)


def valid_csv(filename):
    csv_file = open(filename)
    csv_string = csv_file.read().decode('utf-8')
    csv_file.close()
    csv_validator = UsersCSV()
    try:
        return csv_validator.to_python(csv_string, None)
    except formencode.Invalid as e:
        print u"Invalid csv: %s" % unicode(e.msg).replace('<br />', '\n')
        sys.exit(1)


def print_invite_result(data, reinvite=False):
    if len(data['users']) != 0:
        for user in data['users']:
            if user.user_name in data['not_created'] or \
               user.user_name in data['not_mailed']:
                print(u"Errors while %sinviting user %s:" %
                      (u're' if reinvite else u'', user.user_name))
                if user.user_name in data['not_created']:
                    print(u"    not created")
                if user.user_name in data['not_mailed']:
                    print(u"    not mailed")
            else:
                print(u"%sinvited user %s" %
                      (u're' if reinvite else u'', user.user_name))
    else:
        print(u"No users to reinvite")


def main():
    args = parse_args()
    load_config(args.conf_file)

    if args.instance is None:
        instance = None
    else:
        instance = valid_instance(args.instance)
    invited_badge = valid_userbadge(args.badge.decode('utf-8'), instance)
    creator = User.find(u'admin')

    if args.action == u'invite':
        template = valid_template(args.template)
        csv_data = valid_csv(args.csv_file)
        for user_info in csv_data:
            user_info[u'user_badges'].add(invited_badge)

        ret = user_import(csv_data, args.subject, template, creator, instance)
        print_invite_result(ret)
    elif args.action == u'reinvite':
        template = valid_template(args.template)

        users = invited_users(invited_badge, activated=False)
        csv_data = [{
                    u'email': u.email,
                    u'user_name': u.user_name,
                    u'display_name': u.display_name,
                    u'user_badges': set(),
                    } for u in users]

        ret = user_import(csv_data, args.subject, template, creator, instance,
                          reinvite=True)
        print_invite_result(ret, reinvite=True)
    elif args.action == u'revoke':
        users = invited_users(invited_badge, activated=False)
        if len(users) != 0:
            for user in users:
                revoke(user)
        else:
            print(u"No users to revoke")
    elif args.action == u'uninvite':
        if len(args.users) != 0:
            for name in args.users:
                user = User.find(name)
                uninvite(user, invited_badge, revoke=args.revoke)
        else:
            print(u"No users to uninvite")

    meta.Session.commit()


if __name__ == '__main__':
    sys.exit(main())
