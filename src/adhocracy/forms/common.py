import csv
from datetime import datetime
import re
from StringIO import StringIO
from PIL import Image

import formencode
from pylons import tmpl_context as c
from pylons.i18n import _
from webhelpers.html import literal

from sqlalchemy import func

from adhocracy import config
from adhocracy.lib.auth import can
from adhocracy.lib.unicode import UnicodeDictReader


FORBIDDEN_NAMES = ["www", "static", "mail", "edit", "create", "settings",
                   "join", "leave", "control", "test", "support", "page",
                   "proposal", "wiki", "blog", "proposals", "admin", "dl",
                   "downloads", "stats", "branch", "merge", "pull", "push",
                   "hg", "git", "adhocracy", "user", "openid", "auth", "watch",
                   "poll", "delegation", "event", "comment", "root", "search",
                   "tag", "svn", "trac", "lists", "list", "new", "update",
                   "variant", "provision", "untag", "code", "sso", "velruse"]


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
        if (c.user is not None and c.user.email is not None
           and c.user.email.lower() == value.lower()):
            return value
        from adhocracy.model import User
        if User.all_q()\
                .filter(func.lower(User.email) == value.lower()).count():
            raise formencode.Invalid(
                _('That email is already used by another account'),
                value, state)
        return value


class ValidLocale(formencode.FancyValidator):
    def _to_python(self, value, state):
        from adhocracy import i18n
        if value in i18n.LOCALE_STRINGS:
            return value
        else:
            raise formencode.Invalid(_('Invalid locale choice'), value, state)


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


class StaticPageKey(formencode.FancyValidator):
    def to_python(self, value, state):
        from adhocracy.lib import staticpage
        if not value:
            raise formencode.Invalid(
                _('No static key is given'),
                value, state)
        if not staticpage.STATICPAGE_KEY.match(value) or value in ['new']:
            raise formencode.Invalid(
                _('The static key is invalid'),
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
        if can.badge.manage_global() or can.badge.edit_global():
            if value:
                instance = Instance.find(value)
                if instance is None:
                    raise AssertionError("Could not find instance %s" % value)
                return instance
            return None
        elif can.badge.manage_instance() or can.badge.edit_instance():
            instance = Instance.find(value)
            if instance is not None and instance == c.instance:
                return instance
        raise formencode.Invalid(
            _("You're not allowed to edit global badges"),
            value, state)


class ValidUserBadge(formencode.FancyValidator):

    def _to_python(self, value, state):
        from adhocracy.model import UserBadge
        badge = UserBadge.by_id(value, instance_filter=False)
        if badge is None or badge.instance not in [None, c.instance]:
            raise formencode.Invalid(
                _("No Badge ID '%s' exists") % value,
                value, state)
        return badge


class ValidUserBadges(formencode.FancyValidator):
    """ Check for a set of user badges, inputted by ID """

    accept_iterator = True

    def __init__(self, not_empty=False):
        super(formencode.FancyValidator, self).__init__()
        self.not_empty = not_empty
        if not not_empty:
            self.if_missing = []

    def _to_python(self, value, state):
        from adhocracy.model import UserBadge

        if value is None:
            if self.not_empty:
                raise formencode.Invalid(_('No badges selected'), value, state)

            return []

        if isinstance(value, (str, unicode)):
            value = [value]

        if len(value) != len(set(value)):
            raise formencode.Invalid(
                _("Duplicates in input set of user badge IDs"),
                value, state)

        if self.not_empty and not value:
            raise formencode.Invalid(_('No badges selected'), value, state)

        badges = UserBadge.findall_by_ids(value)
        if len(badges) != len(value):
            missing = set(value).difference(b.id for b in badges)
            raise formencode.Invalid(
                _("Could not find badges %s") % ','.join(map(str, missing)),
                value, state)
        return badges


class ValidUserBadgeNames(formencode.FancyValidator):

    def __init__(self, instance_filter=True, **kwargs):
        super(formencode.FancyValidator, self).__init__(**kwargs)
        self.instance_filter = instance_filter

    def _to_python(self, value, state):
        from adhocracy.model import UserBadge

        if value is None or value == '':
            return []

        labels = [l.strip() for l in value.split(',')]

        if len(labels) != len(set(labels)):
            raise formencode.Invalid(
                _("Duplicates in input set of user badge labels"),
                value, state)

        badges = set()
        missing = set()

        for label in labels:
            badge = UserBadge.find(label, instance_filter=self.instance_filter)
            if badge is None:
                missing.add(label)
            else:
                badges.add(badge)

        if missing:
            raise formencode.Invalid(
                _("Could not find badges %s") % ','.join(missing),
                value, state)
        else:
            return badges


class ValidInstanceBadge(formencode.FancyValidator):

    def _to_python(self, value, state):
        from adhocracy.model import InstanceBadge
        try:
            value = int(value)
        except ValueError:
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


class ValidThumbnailBadge(formencode.FancyValidator):

    def _to_python(self, value, state):
        from adhocracy.model import ThumbnailBadge
        try:
            value = int(value)
        except:
            pass
        badge = ThumbnailBadge.by_id(value, instance_filter=False)
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
        if badge.instance is None and c.instance is not None\
           and c.instance.hide_global_categories:
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
            raise formencode.Invalid(_("No name is given."),
                                     value, state)

        if (var.lower() in FORBIDDEN_NAMES or not
                VALIDVARIANT.match(var.lower())):
            raise formencode.Invalid(_("Invalid name: %s") % value,
                                     value, state)
        try:
            int(var)
            raise formencode.Invalid(
                _("Name cannot be purely numeric: %s") % value,
                value, state)
        except:
            return var


class ValidRegion(formencode.FancyValidator):
    def _to_python(self, value, state):
        from adhocracy.model import meta, Region
        r = meta.Session.query(Region).filter(Region.id == value).first()
        if r is None:
            raise formencode.Invalid(_(u'Invalid region: %s') % value,
                                     value, state)
        return value


class UnusedTitle(formencode.validators.String):
    def __init__(self):
        super(UnusedTitle, self).__init__(min=3, max=254, not_empty=True)

    def _to_python(self, value, state):
        from adhocracy.model import Page
        value = super(UnusedTitle, self)._to_python(value, state)

        if hasattr(state, 'page') and state.page.label == value:
            return value

        if not Page.unusedTitle(value):
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


class UnusedProposalTitle(formencode.validators.FormValidator):

    def validate_python(self, field_dict, state):
        from adhocracy.model import Page

        value = field_dict['label']

        if hasattr(state, 'page') and state.page.label == value:
            return value

        if hasattr(state, 'page'):  # edit
            proposal = state.page.proposal
            is_amendment = proposal.is_amendment
            page = proposal.selection if is_amendment else None
        else:  # new
            is_amendment = field_dict['amendment']
            page = field_dict['page'][0]['id'] if is_amendment else None
        if not Page.unusedTitle(value, selection=page):
            msg = _("An entry with this title already exists")
            raise formencode.Invalid(
                msg, field_dict, state,
                error_dict={'label': msg}
            )

        if not value or len(value) < 2:
            msg = _("No page name is given.")
            raise formencode.Invalid(
                msg, field_dict, state,
                error_dict={'label': msg}
            )

        if value.lower() in FORBIDDEN_NAMES:
            msg = _("Invalid entry name: %s") % value
            raise formencode.Invalid(
                msg, field_dict, state,
                error_dict={'label': msg}
            )

        # every proposal title must be a valid variant name
        try:
            variant_name_validator = VariantName()
            variant_name_validator._to_python(value, state)
        except formencode.Invalid as e:
            raise formencode.Invalid(
                e.msg, field_dict, state,
                error_dict={'label': e.msg}
            )

        try:
            int(value)
            msg = _("Entry name cannot be purely numeric: %s") % value
            raise formencode.Invalid(
                msg, field_dict, state,
                error_dict={'label': msg}
            )
        except ValueError:
            return field_dict


class ProposalMessageNoRecipientGroup(formencode.validators.FormValidator):

    def validate_python(self, field_dict, state):
        if (not field_dict.get('creators', False) and
                not field_dict.get('supporters', False) and
                not field_dict.get('opponents', False)):
            msg = _(u"Please select at least one recipient group")
            raise formencode.Invalid(
                msg, field_dict, state,
                error_dict={'creators': msg}
            )

USER_NAME = 'user_name'
DISPLAY_NAME = 'display_name'
EMAIL = 'email'
USER_BADGES = 'user_badges'
USERNAME_VALIDATOR = formencode.All(
    formencode.validators.PlainText(not_empty=True),
    UniqueUsername(),
    ContainsChar())
EMAIL_VALIDATOR = formencode.All(formencode.validators.Email(not_empty=True),
                                 UniqueEmail())


class UsersCSV(formencode.FancyValidator):

    def to_python(self, value, state=None):
        if state is None:
            global_admin = False
        else:
            global_admin = getattr(state, u'global_admin', False)
        fieldnames = [USER_NAME, DISPLAY_NAME, EMAIL, USER_BADGES]
        errors = []
        items = []
        self.usernames = {}
        self.emails = {}
        self.duplicates = False
        value = value.encode('utf-8')
        reader = UnicodeDictReader(StringIO(value), fieldnames=fieldnames)
        try:
            for item in reader:
                error_list, cleaned_item = self._check_item(
                    item, reader.line_num, global_admin=global_admin)
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

    def _check_item(self, item, line, global_admin=False):
        error_list = []
        user_name = item.get(USER_NAME, '').strip()
        email = item.get(EMAIL, '')
        badges = item.get(USER_BADGES, '')
        if email is not None:
            email = email.strip()
        validated = {}
        USERBADGE_VALIDATOR = ValidUserBadgeNames(
            not_empty=False, if_empty=[],
            instance_filter=(not global_admin))
        for (validator, value) in ((USERNAME_VALIDATOR, user_name),
                                   (EMAIL_VALIDATOR, email),
                                   (USERBADGE_VALIDATOR, badges),
                                   ):
            try:
                validated[validator] = validator.to_python(value, None)
            except formencode.Invalid, E:
                error_list.append(u'%s (%s)' % (E.msg, value))
        emails = self.emails.setdefault(email, [])
        emails.append(line)
        usernames = self.usernames.setdefault(user_name.strip(), [])
        usernames.append(line)
        if len(emails) > 1 or len(usernames) > 1:
            self.duplicates = True
        cleaned_item = item.copy()
        cleaned_item.update({USER_NAME: user_name,
                             EMAIL: email,
                             USER_BADGES: validated.get(validator),
                             })
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


class ValidImageFileUpload(formencode.FancyValidator):

    max_size = 5 * 1024 * 1024

    def _to_python(self, value, state):
        payload = value.file.read(self.max_size + 1)
        if len(payload) > 0:
            try:
                value.file.seek(0)
                im = Image.open(value.file)
                value.file.seek(0)
                del im
            except IOError:
                raise formencode.Invalid(_("This is not a valid image file"),
                                         value, state)
        return value


class ValidFileUpload(formencode.FancyValidator):

    max_size = 1024 * 1024

    def _to_python(self, value, state):
        payload = value.file.read(self.max_size)
        value.file.seek(0)
        if len(payload) == self.max_size:
            raise formencode.Invalid(_("The file is too big (>1MB)"),
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
                       MassmessageController._get_allowed_instances(c.user))
        if any(int(i) not in allowed_ids for i in value):
            raise formencode.Invalid(
                _('Disallowed instance selected'), value, state)

        return value


def ProposalSortOrder():
    from adhocracy.lib.pager import PROPOSAL_SORTS
    return formencode.validators.OneOf(
        [''] +
        [
            v.value
            for g in PROPOSAL_SORTS.by_group.values()
            for v in g
        ])


class OptionalAttributes(formencode.validators.FormValidator):

    def validate_python(self, field_dict, state):

        optional_attributes = config.get_optional_user_attributes()
        error_dict = {}
        for (key, type_, converter, label, allowed) in optional_attributes:

            if key not in field_dict:
                continue

            value = field_dict[key]

            if value and not isinstance(value, type_):
                try:
                    value = converter(value)
                except:
                    error_dict[key] = _(u'Invalid value')
                    continue

            field_dict[key] = value

            if allowed is not None:
                if value not in [a['value'] for a in allowed]:
                    error_dict[key] = _(u'Invalid choice')
                    continue

        if error_dict:
            raise formencode.Invalid(u'_', field_dict, state,
                                     error_dict=error_dict)

        return field_dict


class NotAllFalse(formencode.validators.FormValidator):

    def __init__(self, keys, msg, *args, **kwargs):
        super(NotAllFalse, self).__init__(*args, **kwargs)
        self.keys = keys
        self.msg = msg

    def validate_python(self, field_dict, state):

        if all(not field_dict.get(key, False) for key in self.keys):
            raise formencode.Invalid(
                self.msg, field_dict, state,
                error_dict={self.keys[0]: self.msg}
            )
