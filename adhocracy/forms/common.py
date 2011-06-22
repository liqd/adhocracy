import re

import formencode
from pylons.i18n import _


FORBIDDEN_NAMES = ["www", "static", "mail", "edit", "create", "settings",
                   "join", "leave", "control", "test", "support", "page",
                   "proposal", "wiki", "blog", "proposals", "admin", "dl",
                   "downloads", "stats", "branch", "merge", "pull", "push",
                   "hg", "git", "adhocracy", "user", "openid", "auth", "watch",
                   "poll", "delegation", "event", "comment", "root", "search",
                   "tag", "svn", "trac", "lists", "list", "new", "update",
                   "variant", "provision", "untag"]


VALIDUSER = re.compile(r"^[a-zA-Z0-9_\-]{3,255}$")
VALIDVARIANT = re.compile(r"^[\w\-_ ]{1,255}$", re.U)
TIME = re.compile(r"\d{1,2}.\d{1,2}.\d{4}")

class UniqueUsername(formencode.FancyValidator):
    def _to_python(self, value, state):
        from adhocracy.model import meta, User
        if not value or not isinstance(value, basestring):
            raise formencode.Invalid(
                _('No username is given'),
                value, state)
        if len(value.strip()) < 3:
            raise formencode.Invalid(
                _('Username is too short'),
                value, state)
        if not VALIDUSER.match(value) or value in FORBIDDEN_NAMES:
            raise formencode.Invalid(
                _('The username is invalid'),
                value, state)
        if meta.Session.query(User.user_name).filter(User.user_name ==
                                                     value).all():
            raise formencode.Invalid(
                _('That username already exists'),
                value, state)
        return value


class UniqueEmail(formencode.FancyValidator):
    def _to_python(self, value, state):
        from adhocracy.model import meta, User
        email = value.lower()
        if meta.Session.query(User.email).filter(User.email == email).all():
            raise formencode.Invalid(
                _('That email is already registered'),
                value, state)
        return value


from datetime import datetime
class ValidDate(formencode.FancyValidator):
    def _to_python(self, value, state):
        if not TIME.match(value):
            raise formencode.Invalid(
                _('Invalid date, expecting DD.MM.YYYY'),
                    value, state)
        try:
            return datetime.strptime(value, "%d.%m.%Y")
        except ValueError, ve:
            raise formencode.Invalid(
                _('Invalid date, expecting DD.MM.YYYY'),
                   value, state)
        return value


class ValidHTMLColor(formencode.validators.Regex):

    regex = r'^#[0-9a-fA-F]{1,6}'

    def to_python(self, value, state):
        try:
            super(ValidHTMLColor, self).to_python(value, state)
        except formencode.Invalid:
            raise formencode.Invalid(
                _("Please enter a html color code like '#f0f0f0'. "
                  "'%(value)' is not a valid color code."), value, state)
        return value


class UniqueInstanceKey(formencode.FancyValidator):
    def _to_python(self, value, state):
        from adhocracy.model import Instance
        if not value:
            raise formencode.Invalid(
                _('No instance key is given'),
                value, state)
        if not Instance.INSTANCE_KEY.match(value) or value in FORBIDDEN_NAMES:
            raise formencode.Invalid(
                _('The instance key is invalid'),
                value, state)
        if Instance.find(value):
            raise formencode.Invalid(
                _('An instance with that key already exists'),
                value, state)
        return value


class ValidDelegateable(formencode.FancyValidator):
    def _to_python(self, value, state):
        from adhocracy.model import Delegateable
        delegateable = Delegateable.find(value)
        if not delegateable:
            raise formencode.Invalid(
                _("No entity with ID '%s' exists") % value,
                value, state)
        return delegateable


class ValidProposal(formencode.FancyValidator):
    def _to_python(self, value, state):
        from adhocracy.model import Proposal
        proposal = Proposal.find(value)
        if not proposal:
            raise formencode.Invalid(
                _("No proposal with ID '%s' exists") % value,
                value, state)
        return proposal


class ValidGroup(formencode.FancyValidator):
    def _to_python(self, value, state):
        from adhocracy.model import Group
        group = Group.by_code(value)
        if not group:
            raise formencode.Invalid(
                _("No group with ID '%s' exists") % value,
                value, state)
        return group

class MaybeMilestone(formencode.FancyValidator):
    def _to_python(self, value, state):
        from adhocracy.model import Milestone
        return Milestone.find(value)

class ValidRevision(formencode.FancyValidator):
    def _to_python(self, value, state):
        from adhocracy.model import Revision
        revision = Revision.find(value)
        if not revision:
            raise formencode.Invalid(
                _("No revision with ID '%s' exists") % value,
                value, state)
        return revision


class ValidComment(formencode.FancyValidator):
    def _to_python(self, value, state):
        from adhocracy.model import Comment
        comment = Comment.find(value)
        if not comment:
            raise formencode.Invalid(
                _("No comment with ID '%s' exists") % value,
                value, state)
        return comment


class ValidWatch(formencode.FancyValidator):
    def _to_python(self, value, state):
        from adhocracy.model import Watch
        watch = Watch.by_id(value)
        if not watch:
            raise formencode.Invalid(
                _("No watchlist entry with ID '%s' exists") % value,
                value, state)
        return watch


class ValidRef(formencode.FancyValidator):
    def _to_python(self, value, state):
        from adhocracy.model import refs
        try:
            entity = refs.from_url(value)
            if not entity:
                raise TypeError()
            return entity
        except:
            raise formencode.Invalid(_("Invalid reference"), value, state)


class ExistingUserName(formencode.FancyValidator):
    def _to_python(self, value, state):
        from adhocracy.model import User
        user = User.find(value)
        if not user:
            raise formencode.Invalid(
                _("No user with the user name '%s' exists") % value,
                value, state)
        return user


class ValidTagging(formencode.FancyValidator):
    def _to_python(self, value, state):
        from adhocracy.model import Tagging
        tagging = Tagging.find(value)
        if not tagging:
            raise formencode.Invalid(
                _("No tagging with ID '%s' exists") % value,
                value, state)
        return tagging


class ValidTag(formencode.FancyValidator):
    def _to_python(self, value, state):
        from adhocracy.model import Tag
        tag = Tag.find(value)
        if not tag:
            raise formencode.Invalid(
                _("No tag with ID '%s' exists") % value,
                value, state)
        return tag


class ValidText(formencode.FancyValidator):
    def _to_python(self, value, state):
        from adhocracy.model import Text
        text = Text.find(value)
        if not text:
            raise formencode.Invalid(
                _("No text with ID '%s' exists") % value,
                         value, state)
        return text


class ValidPage(formencode.FancyValidator):
    def _to_python(self, value, state):
        from adhocracy.model import Page
        page = Page.find(value)
        if not page:
            raise formencode.Invalid(_("No page '%s' exists") % value,
                                     value, state)
        return page


class ValidPageFunction(formencode.FancyValidator):
    def _to_python(self, value, state):
        from adhocracy.model import Page
        function = value.lower().strip()
        if function not in Page.FUNCTIONS:
            raise formencode.Invalid(_("Invalid page function: %s") % value,
                                     value, state)
        return function


class VariantName(formencode.FancyValidator):
    def _to_python(self, value, state):
        from adhocracy.lib.text import variant_normalize
        var = variant_normalize(value)
        if not var or len(var) < 2:
            raise formencode.Invalid(_("No variant name is given."),
                                     value, state)

        if (var.lower() in FORBIDDEN_NAMES or not
            VALIDVARIANT.match(var.lower())):
            raise formencode.Invalid(_("Invalid variant name: %s") % value,
                                     value, state)
        try:
            int(var)
            raise formencode.Invalid(
                _("Variant name cannot be purely numeric: %s") % value,
                value, state)
        except:
            return var


class UnusedTitle(formencode.validators.String):
    def __init__(self):
        super(UnusedTitle, self).__init__(min=3, max=254, not_empty=True)

    def _to_python(self, value, state):
        from adhocracy.model import Page
        value = super(UnusedTitle, self)._to_python(value, state)
        page = Page.find_fuzzy(value)
        if hasattr(state, 'page') and state.page == page:
            return value

        if page is not None:
            raise formencode.Invalid(
                _("An entry with this title already exists"), value, state)

        if not value or len(value) < 2:
            raise formencode.Invalid(_("No page name is given."), value, state)

        if value.lower() in FORBIDDEN_NAMES:
            raise formencode.Invalid(_("Invalid page name: %s") % value,
                                     value, state)

        try:
            int(value)
            raise formencode.Invalid(
                _("Variant name cannot be purely numeric: %s") % value,
                value, state)
        except:
            return value
