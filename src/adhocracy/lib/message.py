from adhocracy.i18n import _
from pylons import config


def render_body(body, recipient, include_footer, is_preview=False):
    from adhocracy.lib import helpers as h
    from adhocracy.lib.templating import render
    from adhocracy.lib.auth.welcome import welcome_url

    if recipient.gender == 'f':
        salutation = _('Dear Ms.')
    elif recipient.gender == 'm':
        salutation = _('Dear Mr.')
    else:
        salutation = _('Dear')

    if is_preview:
        welcome_url = welcome_url(recipient,
                                  (u'X' * len(recipient.welcome_code)
                                   if recipient.welcome_code
                                   else u'NO_WELCOME_CODE_SET'))
    else:
        welcome_url = welcome_url(recipient, recipient.welcome_code)

    rendered_body = body.format(**{
        'name': recipient.name,
        'email': recipient.email,
        'welcome_url': welcome_url,
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
