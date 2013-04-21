from adhocracy.i18n import _
from pylons import config

def render_body(body, recipient, include_footer):
    from adhocracy.lib import helpers as h
    from adhocracy.lib.templating import render
    from adhocracy.lib.auth.welcome import welcome_url

    if recipient.gender == 'f':
        salutation = _('Dear Ms.')
    elif recipient.gender == 'm':
        salutation = _('Dear Mr.')
    else:
        salutation = _('Dear')

    rendered_body = body.format(**{
        'name': user.name,
        'email': user.email,
        'welcome_link': welcome_url(user, user.welcome_code),
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
