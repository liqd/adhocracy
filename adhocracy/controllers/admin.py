from datetime import datetime

from pylons.i18n import _

from adhocracy.lib.base import *

log = logging.getLogger(__name__)

class AdminController(BaseController):

    @RequireInternalRequest()
    @ActionProtector(has_permission("global.admin"))
    def permissions(self):
        if request.method == "POST":
            groups = model.Group.all()
            for permission in model.Permission.all():
                for group in groups:
                    t = request.params.get("%s-%s" % (
                            group.code, permission.permission_name))
                    if t and permission not in group.permissions:
                        group.permissions.append(permission)
                    elif not t and permission in group.permissions:
                        group.permissions.remove(permission)
            for group in groups:
                model.meta.Session.add(group)
            model.meta.Session.commit()
        return render("/admin/permissions.html")

