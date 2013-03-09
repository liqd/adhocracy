import logging

from pylons import tmpl_context as c
from pylons import request

from sqlalchemy import or_
from sqlalchemy.orm import eagerload
from sqlalchemy.orm.exc import NoResultFound

from repoze.what.predicates import has_permission as what_has_permission
from repoze.what.adapters import SourceError
from repoze.what.plugins.sql.adapters import SqlGroupsAdapter

import adhocracy.model as model


log = logging.getLogger(__name__)


NOT_LOGGED_IN = 'not_logged_in'


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
        sections = super(InstanceGroupSourceAdapter,
                         self)._find_sections(credentials)
        sections.add(u"Anonymous")
        return sections

    def _get_item_as_row(self, item_name):
        q = model.meta.Session.query(model.User)
        q = q.filter(model.User.user_name == unicode(item_name))
        q = q.options(eagerload(model.User.memberships))

        try:
            return q.one()
        except NoResultFound, e:
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


class has_default_permission(what_has_permission):
    """
    Checks whether a member of the default group of the given instance has the
    given permission.
    """

    def evaluate(self, environ, credentials):
        if environ.get('default_permissions') is None:
            if c.instance is not None:
                default_group = c.instance.default_group
            else:
                default = model.Group.INSTANCE_DEFAULT
                default_group = model.Group.by_code(default)
            environ['default_permissions'] = [p.permission_name for p in
                                              default_group.permissions]
        if not self.permission_name in environ['default_permissions']:
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
        self.need_valid_email = False

    def __repr__(self):
        return 'AuthCheck for %s' % (self.method)

    def __nonzero__(self):
        return not (self.permission_refusals or self.other_refusals
                    or self.need_valid_email)

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

    def valid_email(self):
        if (c.instance is not None
                and c.user is not None
                and c.instance.require_valid_email
                and not c.user.is_email_activated()):
            self.need_valid_email = True

    def permission_missing(self):
        """ Determines whether a permission is missing. """
        return len(self.permission_refusals) > 0

    def need_login(self):
        """
        Login is needed in case a permission refusal exists and the user is
        not logged in.
        """
        return c.user is None and (self.permission_missing() or
                                   NOT_LOGGED_IN in self.other_refusals)

    def _propose_join_or_login(self):
        """
        Only propose to join or login if there are only permission problems
        and if they would be resolved if the user joined or logged in.
        """
        return (self.permission_refusals
                and not self.other_refusals
                and all(has_default_permission(perm).is_met(request.environ)
                        for perm in self.permission_refusals))

    def propose_login(self):
        """
        Login is proposed if the user isn't logged in or hasn't joined
        c.instance, but a registered user with default instance permissions
        would be able to perform the action.
        """
        return c.user is None and self._propose_join_or_login()

    def propose_join(self):
        """
        Login is proposed if the user is logged in, but not member of the
        instance and can therefore not perform the requested action.
        """
        return (c.user is not None
                and not c.user.is_member(c.instance)
                and self._propose_join_or_login())

    def propose_validate_email(self):
        """
        Email validation is proposed if the user is logged in, but doesn't
        have a valid email address.
        """
        return (not self.permission_refusals
                and not self.other_refusals
                and self.need_valid_email)
