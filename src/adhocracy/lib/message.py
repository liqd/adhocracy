from adhocracy.i18n import _

def render_body(body, user):
    from adhocracy.lib.auth.welcome import welcome_url

    if user.gender == 'f':
        salutation = _('Dear Ms.')
    elif user.gender == 'm':
        salutation = _('Dear Mr.')
    else:
        salutation = _('Dear')

    return body.format(**{
        'name': user.name,
        'email': user.email,
        'welcome_link': welcome_url(user, user.welcome_code),
        'salutation': salutation,
    })
