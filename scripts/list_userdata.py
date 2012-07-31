#!/usr/bin/env python
"""
List data of existing users. The default template lists the username
and email address.
"""
from datetime import datetime

from sqlalchemy import and_, or_

from adhocracy.model import Membership, User

# boilerplate code. copy that
import os
import sys
sys.path.insert(0,  os.path.abspath(os.path.dirname(__file__)))
from common import create_parser, get_instances, load_from_args
# /end boilerplate code

section = 'content'
template = u"{name} <{email}>"
user_info_attrs = ['id',
                   'name',
                   'display_name',
                   'user_name',
                   'email',
                   'locale',
                   'email_priority',
                   'create_time',
                   ]
possible_attrs = ', '.join(user_info_attrs)


def main():
    parser = create_parser(description=__doc__)
    parser.add_argument(
        "-t", dest="template", default=template, type=unicode,
        help=("The template to use. "
              "(default: '%s', possible keys: %s)" % (template,
                                                      possible_attrs)))
    args = parser.parse_args()
    load_from_args(args)
    instances = get_instances(args)

    query = User.all_q()

    if instances is not None:
        instance_ids = [instance.id for instance in instances]
        query = query.filter(User.memberships.any(
            and_(Membership.instance_id.in_(instance_ids),
                 or_(Membership.expire_time == None,
                     Membership.expire_time > datetime.utcnow()))))

    for user in query:
        userinfo = user_info(user)
        s = args.template.format(**userinfo)
        print s.encode('utf-8')


def user_info(user):
    info = dict([(attr, getattr(user, attr)) for attr in user_info_attrs])
    return info


if __name__ == '__main__':
    sys.exit(main())
