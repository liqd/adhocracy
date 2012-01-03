import logging

from pylons import request

from repoze.what.plugins.pylonshq import ActionProtector

from adhocracy import model
from adhocracy.lib.auth.authorization import has_permission
from adhocracy.lib.auth.csrf import RequireInternalRequest
from adhocracy.lib.base import BaseController
from adhocracy.lib.templating import render


log = logging.getLogger(__name__)


class AdminController(BaseController):

    def index(self):
        return render("/admin/index.html")

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
