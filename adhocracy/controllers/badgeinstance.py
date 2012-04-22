from pylons import tmpl_context as c
from repoze.what.plugins.pylonshq import ControllerProtector
from adhocracy.controllers.badgeglobal import BadgeBaseController
from adhocracy.lib.auth.authorization import has_permission
from adhocracy.lib import helpers as h


@ControllerProtector(has_permission("instance.admin"))
class BadgeinstanceController(BadgeBaseController):
    """Badge controller to allow instance admins
       to change instance badges.
    """

    @property
    def base_url(self):
        return h.entity_url(c.instance) + "/badge"
