from decorator import decorator

from pylons import tmpl_context as c
from pylons.controllers.util import abort
from pylons.i18n import _

from adhocracy.lib.instance.discriminator import setup_discriminator


def _RequireInstance(f, *a, **kw):
    if not c.instance:
        abort(400, _("This action is only available in an instance context."))
    else:
        return f(*a, **kw)

RequireInstance = decorator(_RequireInstance)
