from adhocracy.i18n import _
from adhocracy.lib.helpers import base_url


def _make_welcome_link(user):
    return base_url("/welcome/%s/%s" % (user.user_name, user.welcome_code),
                    absolute=True)


def render_body(body, user):
    if user.gender == 'f':
        salutation = _('Dear Ms.')
    elif user.gender == 'm':
        salutation = _('Dear Mr.')
    else:
        salutation = _('Dear')

    return body.format(**{
        'name': user.name,
        'email': user.email,
        'welcome_link': _make_welcome_link(user),
        'salutation': salutation,
    })
