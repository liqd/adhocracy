#!/usr/bin/env python
"""
Extract email adresses from adhocracy. Emails from deleted users won't be
exported.
"""
from datetime import datetime

from sqlalchemy import and_, or_

from adhocracy.model import Group, Membership, meta, User

# boilerplate code. copy that
import os
import sys
sys.path.insert(0,  os.path.abspath(os.path.dirname(__file__)))
from common import create_parser, get_instances, load_from_args
# /end boilerplate code


def main():
    parser = create_parser(description=__doc__, use_instance=False)
    parser.add_argument(
        "username",
        help=("The name of the user who should become a global admin"))
    args = parser.parse_args()
    load_from_args(args)

    user = User.find(args.username)
    if user is None:
        print 'Cannot find user %s\n' % args.username
        parser.exit()

    global_membership = [membership for membership in user.memberships if
                         membership.instance is None][0]
    admin_group = Group.by_code(Group.CODE_ADMIN)
    global_membership.group = admin_group
    meta.Session.commit()
if __name__ == '__main__':
    sys.exit(main())
