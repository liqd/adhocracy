from adhocracy.model.velruse import Velruse
from pylons import tmpl_context as c


def is_user_connected_to_facebook():
    return Velruse.by_user_and_domain(c.user, u'facebook.com') != []


def facebook_account():
    return Velruse.by_user_and_domain_first(c.user, u'facebook.com')
