from adhocracy.i18n import _
from adhocracy.lib.helpers import base_url

from pylons import config


def _make_welcome_link(user):
    return base_url("/welcome/%s/%s" % (user.user_name, user.welcome_code),
                    absolute=True)


def render_body(body, recipient, include_footer):
    from adhocracy.lib import helpers as h
    from adhocracy.lib.templating import render

    if recipient.gender == 'f':
        salutation = _('Dear Ms.')
    elif recipient.gender == 'm':
        salutation = _('Dear Mr.')
    else:
        salutation = _('Dear')

    rendered_body = body.format(**{
        'name': recipient.name,
        'email': recipient.email,
        'welcome_link': _make_welcome_link(recipient),
        'salutation': salutation,
    })

    return render("/massmessage/body.txt", {
        'body': rendered_body,
        'page_url': config.get('adhocracy.domain').strip(),
        'settings_url': h.entity_url(recipient,
                                     member='edit',
                                     absolute=True),
        'include_footer': include_footer,
    })
