import logging

from pylons import tmpl_context as c
from pylons import request

from sqlalchemy import or_
from sqlalchemy.orm import eagerload

from repoze.what.predicates import has_permission as what_has_permission
from repoze.what.adapters import SourceError
from repoze.what.plugins.sql.adapters import SqlGroupsAdapter

import adhocracy.model as model


log = logging.getLogger(__name__)


class InstanceGroupSourceAdapter(SqlGroupsAdapter):

    def __init__(self, *args, **kwargs):
        super(InstanceGroupSourceAdapter, self).__init__(model.Group,
                                                         model.User,
                                                         model.meta.Session)
        self.is_writable = False

    def _get_section_items(self, section):
        q = model.meta.Session.query(model.User.user_name)
        q = q.join(model.Membership)
        q = q.join(model.Group)
        q = q.filter(model.Group.code == section)
        q = q.filter(
            or_(model.Membership.instance == None,
                model.Membership.instance == model.filter.get_instance()))
        return q.all()

    def _find_sections(self, credentials):
        sections = list(super(InstanceGroupSourceAdapter,
                              self)._find_sections(credentials))
        sections.append(u"Anonymous")
        return set(sections)

    def _get_item_as_row(self, item_name):
        q = model.meta.Session.query(model.User)
        q = q.filter(model.User.user_name == unicode(item_name))
        q = q.options(eagerload(model.User.memberships))
        try:
            return q.limit(1).first()
        except Exception, e:
            log.exception(e)
            raise SourceError("No such user: %s" % item_name)


class has_permission(what_has_permission):
    """
    This modified version of ``repoze.what``'s ``has_permission`` will
    apply ``Anonymous`` rights to any user making requests. This allows
    to call ``has_permission`` on methods even when they are not protected,
    thus making the authorization system more configurable.
    """

    def evaluate(self, environ, credentials):
        if c.user:
            super(has_permission, self).evaluate(environ, credentials)
        else:
            if environ.get('anonymous_permissions') is None:
                anon_group = model.Group.by_code(model.Group.CODE_ANONYMOUS)
                environ['anonymous_permissions'] = [p.permission_name for p in
                                                    anon_group.permissions]
            if not self.permission_name in environ['anonymous_permissions']:
                self.unmet()


def has(permission):
    #return permission in request.environ.get('repoze.what.credentials',
    #{}).get('permissions', [])
    p = has_permission(permission)
    return p.is_met(request.environ)


class AuthCheck(object):
    """
    AuthCheck collects reasons for authorisation refusals in two sets:
    ``permission_refusals`` and ``other_refusals``. It evaluates to True in
    case authorisation is granted, otherwise False.
    """

    # IDEA: Collect fulfilled authorisation checks as well

    def __init__(self, method):
        self.method = method
        self.permission_refusals = set()
        self.other_refusals = set()

    def __repr__(self):
        return 'AuthCheck for %s' % (self.method)

    def __nonzero__(self):
        return not (self.permission_refusals or self.other_refusals)

    def perm(self, permission):
        """
        Convenience function performing a permission check, which adds the
        permission to ``self.permission_refusal``.
        """
        if not has(permission):
            self.permission_refusals.add(permission)

    def other(self, label, value):
        """
        Convenience function, which adds a refusal label to
        ``self.other_refusals`` in case the given value is ``True``.
        """
        if value is True:
            self.other_refusals.add(label)
