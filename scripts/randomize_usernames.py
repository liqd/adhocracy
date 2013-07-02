"""
This script randomizes all user ids by using the
adhocracy.lib.util.random_username function.

Run from within a paster environment.
"""

import sys

from sqlalchemy import not_

from adhocracy.model import meta
from adhocracy.model.user import User
from adhocracy.lib.util import random_username


EXCLUDED_USERNAMES = ['admin', 'nidi']
SET_DISPLAY_NAMES = True


def main():
    users = User.all_q(include_deleted=None)\
        .filter(not_(User.user_name.in_(EXCLUDED_USERNAMES))).all()

    for user in users:
        user_name = None
        while user_name is None:
            try_user_name = random_username()
            if User.find(try_user_name) is None:
                user_name = try_user_name
        if SET_DISPLAY_NAMES and user.display_name is None:
            user.display_name = user.user_name
        user.user_name = user_name
        meta.Session.flush()

    meta.Session.commit()


if __name__ == '__main__':
    sys.exit(main())
