import logging

from adhocracy import model
from adhocracy.lib.helpers import base_url, has_permission
from adhocracy.lib.mail import to_user
from adhocracy.lib.util import random_token

log = logging.getLogger(__name__)


def user_import(_users, email_subject, email_template, creator, instance,
                reinvite=False):
    names = []
    created = []
    mailed = []
    errors = False
    users = []
    for user_info in _users:
        try:
            name = user_info['user_name']
            email = user_info['email']

            try:
                display_name = user_info['display_name']
                names.append(name)
                if reinvite:
                    user = model.User.find(name)
                else:
                    user = model.User.create(name, email,
                                             display_name=display_name,
                                             autojoin=False)
                    user.activation_code = user.IMPORT_MARKER + random_token()
                password = random_token()
                user_info['password'] = password
                user.password = password

                for badge in user_info['user_badges']:
                    badge.assign(user, creator=creator)

                model.meta.Session.add(user)
                model.meta.Session.commit()
                users.append(user)
                created.append(user.user_name)
                url = base_url(
                    "/user/%s/activate?c=%s" % (user.user_name,
                                                user.activation_code),
                    instance=instance,
                    absolute=True)

                user_info['url'] = url
                body = email_template.format(*user_info.get('rest', []),
                                             **user_info)
                to_user(user, email_subject, body, decorate_body=False)
                mailed.append(user.user_name)

            except Exception, E:
                log.error('user import for user %s, email %s, exception %s' %
                          (user_info['user_name'], user_info['email'], E))
                errors = True
                continue
        except Exception, E:
            log.error('user import invalid user exception %s' % E)
            errors = True
            continue
    return {
        'users': users,
        'not_created': set(names) - set(created),
        'not_mailed': set(created) - set(mailed),
        'errors': errors
    }


def get_user_import_state():
    """user import state

    This function can be used to generate state objects for formencode.
    """

    class State(object):
        pass

    state = State()
    state.global_admin = has_permission('global.admin')

    return state
