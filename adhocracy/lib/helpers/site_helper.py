from pylons import tmpl_context as c, config
from pylons.i18n import _

def name():
    return config.get('adhocracy.site.name', _("Adhocracy"))