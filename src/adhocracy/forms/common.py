import csv
from datetime import datetime
import re
from StringIO import StringIO

import formencode
from pylons import tmpl_context as c
from pylons.i18n import _
from webhelpers.html import literal

from sqlalchemy import func

from adhocracy.lib.auth.authorization import has
from adhocracy.lib.unicode import UnicodeDictReader


FORBIDDEN_NAMES = ["www", "static", "mail", "edit", "create", "settings",
                   "join", "leave", "control", "test", "support", "page",
                   "proposal", "wiki", "blog", "proposals", "admin", "dl",
                   "downloads", "stats", "branch", "merge", "pull", "push",
                   "hg", "git", "adhocracy", "user", "openid", "auth", "watch",
                   "poll", "delegation", "event", "comment", "root", "search",
                   "tag", "svn", "trac", "lists", "list", "new", "update",
                   "variant", "provision", "untag", "code"]


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
        if meta.Session.query(User.user_name).filter(
            func.lower(User.user_name) == value.lower()
        ).count():
            raise formencode.Invalid(
                _('That username already exists'),
                value, state)
        return value


class UniqueEmail(formencode.FancyValidator):
    def _to_python(self, value, state):
        from adhocracy.model import User
        if User.all_q()\
                .filter(func.lower(User.email) == value.lower()).count():
            raise formencode.Invalid(
                _('That email is already registered'),
                value, state)
        return value


class UniqueOtherEmail(formencode.FancyValidator):
    """
    Check if email is unused or belongs to the current user.
    """
    def _to_python(self, value, state):
        if c.user.email.lower() == value.lower():
            return value
        from adhocracy.model import User
        if User.all_q()\
                .filter(func.lower(User.email) == value.lower()).count():
            raise formencode.Invalid(
                _('That email is already used by another account'),
                value, state)
        return value


class ValidDate(formencode.FancyValidator):
    def _to_python(self, value, state):
        if not TIME.match(value):
            raise formencode.Invalid(
                _('Invalid date, expecting DD.MM.YYYY'),
                value, state)
        try:
            return datetime.strptime(value, "%d.%m.%Y")
        except ValueError:
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


class ValidInstanceGroup(formencode.FancyValidator):
    def _to_python(self, value, state):
        from adhocracy.model import Group
        group = Group.by_code(value)
        if not group:
            raise formencode.Invalid(
                _("No group with ID '%s' exists") % value,
                value, state)
        if not group.is_instance_group():
            raise formencode.Invalid(
                _("Group '%s' is no instance group") % group.code,
                value, state)
        return group


class ContainsChar(formencode.validators.Regex):

    regex = r"[a-zA-Z]"

    def to_python(self, value, state):
        try:
            super(ContainsChar, self).to_python(value, state)
        except formencode.Invalid:
            raise formencode.Invalid(_("At least one character is required"),
                                     value, state)
        return value


class ValidBadgeInstance(formencode.FancyValidator):

    def _to_python(self, value, state):
        from adhocracy.model import Instance
        if has('global.admin'):
            if value:
                instance = Instance.find(value)
                if instance is None:
                    raise AssertionError("Could not find instance %s" % value)
                return instance
            return None
        elif has('instance.admin') and c.instance:
            return c.instance
        raise formencode.Invalid(
            _("You're not allowed to edit global badges"),
            value, state)


class ValidUserBadge(formencode.FancyValidator):

    def _to_python(self, value, state):
        from adhocracy.model import UserBadge
        badge = UserBadge.by_id(value)
        if not badge:
            raise formencode.Invalid(
                _("No Badge ID '%s' exists") % value,
                value, state)
        return badge


class ValidInstanceBadge(formencode.FancyValidator):

    def _to_python(self, value, state):
        from adhocracy.model import InstanceBadge
        try:
            value = int(value)
        except:
            pass
        badge = InstanceBadge.by_id(value, instance_filter=False)
        if badge is None or badge.instance not in [None, c.instance]:
            raise formencode.Invalid(
                _("No Badge ID '%s' exists") % value,
                value, state)
        return badge


class ValidDelegateableBadge(formencode.FancyValidator):

    def _to_python(self, value, state):
        from adhocracy.model import DelegateableBadge
        try:
            value = int(value)
        except:
            pass
        badge = DelegateableBadge.by_id(value, instance_filter=False)
        if badge is None or badge.instance not in [None, c.instance]:
            raise formencode.Invalid(
                _("No Badge ID '%s' exists") % value,
                value, state)
        return badge


class ValidCategoryBadge(formencode.FancyValidator):

    def _to_python(self, value, state):
        from adhocracy.model import CategoryBadge
        try:
            value = int(value)
        except:
            pass
        badge = CategoryBadge.by_id(value, instance_filter=False)
        if badge is None:
            raise formencode.Invalid(
                _("No Badge ID '%s' exists") % value,
                value, state)
        if badge.instance is None and c.instance.hide_global_categories:
            raise formencode.Invalid(
                _("Cannot use global category %s in this instance") % value,
                value, state)
        if badge.instance not in [None, c.instance]:
            raise formencode.Invalid(
                _("Badge with ID '%s' not valid in this instance") % value,
                value, state)
        return badge


class ValidParentCategory(formencode.validators.FormValidator):

    def validate_python(self, field_dict, state):
        if (field_dict['parent'] is not None and
           field_dict['parent'].instance is not field_dict['instance']):
            msg = _("Parent and child category instance have to match")
            raise formencode.Invalid(
                msg, field_dict, state,
                error_dict={'parent': msg}
            )
        else:
            return field_dict


class ValidateNoCycle(formencode.validators.FormValidator):

    def validate_python(self, field_dict, state):

        def parent_okay(category):
            if category is None:
                # no cycle
                return True
            elif category == field_dict['id']:
                # cycle
                return False
            else:
                return parent_okay(category.parent)

        if parent_okay(field_dict['parent']):
            return field_dict
        else:
            msg = _('You shall not create cycles!')
            raise formencode.Invalid(
                msg, field_dict, state,
                error_dict={'parent': msg}
            )


class MaybeMilestone(formencode.FancyValidator):
    def _to_python(self, value, state):
        from adhocracy.model import Milestone
        try:
            return Milestone.find(value)
        except Exception:
            return None


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


USER_NAME = 'user_name'
DISPLAY_NAME = 'display_name'
EMAIL = 'email'
USERNAME_VALIDATOR = formencode.All(
    formencode.validators.PlainText(not_empty=True),
    UniqueUsername(),
    ContainsChar())
EMAIL_VALIDATOR = formencode.All(formencode.validators.Email(not_empty=True),
                                 UniqueEmail())


class UsersCSV(formencode.FancyValidator):

    def to_python(self, value, state):
        fieldnames = [USER_NAME, DISPLAY_NAME, EMAIL]
        errors = []
        items = []
        self.usernames = {}
        self.emails = {}
        self.duplicates = False
        value = value.encode('utf-8')
        reader = UnicodeDictReader(StringIO(value), fieldnames=fieldnames)
        try:
            for item in reader:
                error_list, cleaned_item = self._check_item(item,
                                                            reader.line_num)
                if error_list:
                    errors.append((reader.line_num, error_list))
                if not errors:
                    items.append(cleaned_item)
        except csv.Error, E:
            line_content = value.split('\n')[reader.line_num]
            msg = _('Error "%(error)s" while reading line '
                    '<pre><i>%(line_content)s</i></pre>') % dict(
                        line_content=line_content,
                        error=str(E))
            errors.append((reader.line_num + 1, [msg]))
        if errors or self.duplicates:
            error_msg = _('The following errors occured while reading '
                          'the list of users: <br />%s')
            line_error_messages = []
            for (line, messages) in errors:
                line_error_messages.append(
                    _('Line %s: %s') % (line, ', '.join(messages)))

            # Insert messages for duplicate emails and usernames
            self._insert_duplicate_messages(
                line_error_messages,
                self.emails,
                _('Email %s is used multiple times'))
            self._insert_duplicate_messages(
                line_error_messages,
                self.usernames,
                _('Username %s is used multiple times'))
            error_msg = error_msg % ('<br />'.join(line_error_messages))
            raise formencode.Invalid(literal(error_msg), value, state)
        else:
            return items

    def _insert_duplicate_messages(self, line_error_messages, duplicate_dict,
                                   msg_template):
        for (value, lines) in duplicate_dict.items():
            if len(lines) > 1:
                lines = [str(line) for line in lines]
                line_error_messages.append(
                    _('Lines %s: %s') % (
                        ', '.join(lines),
                        msg_template % value))

    def _check_item(self, item, line):
        error_list = []
        user_name = item.get(USER_NAME, '').strip()
        email = item.get(EMAIL, '').strip()
        for (validator, value) in ((USERNAME_VALIDATOR, user_name),
                                   (EMAIL_VALIDATOR, email)):
            try:
                validator.to_python(value, None)
            except formencode.Invalid, E:
                error_list.append(u'%s (%s)' % (E.msg, value))
        emails = self.emails.setdefault(email.strip(), [])
        emails.append(line)
        usernames = self.usernames.setdefault(user_name.strip(), [])
        usernames.append(line)
        if len(emails) > 1 or len(usernames) > 1:
            self.duplicates = True
        cleaned_item = item.copy()
        cleaned_item.update({USER_NAME: user_name,
                             EMAIL: email})
        return error_list, cleaned_item


class ContainsEMailPlaceholders(formencode.FancyValidator):

    def _to_python(self, value, state):
        required = ['{url}', '{user_name}', '{password}']
        missing = []
        for s in required:
            if s not in value:
                missing.append(s)
        if missing != []:
            raise formencode.Invalid(
                _('You need to insert the following placeholders into '
                  'the email text so we can insert enough information '
                  'for the user: %s') % ', '.join(missing),
                value, state)
        return value


class MessageableInstances(formencode.FancyValidator):
    """
    Check if the given instance can be mass messaged by the current user.
    """

    accept_iterator = True

    def _to_python(self, value, state):

        if not value:
            raise formencode.Invalid(
                _('Please select at least one instance'), value, state)

        if not isinstance(value, list):
            value = [value]

        from adhocracy.controllers.massmessage import MassmessageController
        allowed_ids = (i.id for i in
                       MassmessageController.get_allowed_instances(c.user))
        if any(int(i) not in allowed_ids for i in value):
            raise formencode.Invalid(
                _('Disallowed instance selected'), value, state)

        return value
