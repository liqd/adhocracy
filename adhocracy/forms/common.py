import re
import formencode
from formencode import validators, foreach

from pylons.i18n.translation import *

from adhocracy.model import *

FORBIDDEN_NAMES = ["www", "static", "mail", "edit", "create", "settings", "join", "leave", 
                   "control", "test", "support", "page", "issue", "proposal", "wiki", 
                   "blog", "issues", "proposals", "admin", "dl", "downloads", "stats",
                   "adhocracy", "user", "openid", "auth", "watch", "poll", "delegation",
                   "event", "comment", "root", "search", "tag", "svn", "trac", "lists", 
                   "list"]

VALIDUSER = re.compile("^[a-zA-Z0-9_\-]{3,255}$")
class UniqueUsername(formencode.FancyValidator):
    def _to_python(self, value, state):
        if not value or not isinstance(value, basestring):
            raise formencode.Invalid(
                _('No username is given'),
                value, state)
        if len(value) < 3:
            raise formencode.Invalid(
                _('Username is too short'),
                value, state)
        if not VALIDUSER.match(value) or value in FORBIDDEN_NAMES:
            raise formencode.Invalid(
                _('The username is invalid'),
                value, state)
        if meta.Session.query(user.User.user_name).filter(user.User.user_name == value).all():
            raise formencode.Invalid(
                _('That username already exists'),
                value, state)
        return value

class UniqueEmail(formencode.FancyValidator):
    def _to_python(self, value, state):
        email = value.lower()
        if meta.Session.query(User.email).filter(User.email == email).all():
            raise formencode.Invalid(
                _('That email is already registered'),
                value, state)
        return value

class UniqueInstanceKey(formencode.FancyValidator):
    def _to_python(self, value, state):
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
        delegateable = Delegateable.find(value)
        if not delegateable: 
           raise formencode.Invalid(
                _("No entity with ID '%s' exists") % value,
                 value, state)
        return delegateable

class ValidIssue(formencode.FancyValidator):
    def _to_python(self, value, state):
        issue = Issue.find(value)
        if not issue: 
           raise formencode.Invalid(
                _("No issue with ID '%s' exists") % value,
                 value, state)
        return issue

class ValidProposal(formencode.FancyValidator):
    def _to_python(self, value, state):
        proposal = Proposal.find(value)
        if not proposal: 
           raise formencode.Invalid(
                _("No proposal with ID '%s' exists") % value,
                 value, state)
        return proposal

class ValidGroup(formencode.FancyValidator):
    def _to_python(self, value, state):
        group = Group.by_code(value)
        if not group: 
           raise formencode.Invalid(
                _("No group with ID '%s' exists") % value,
                 value, state)
        return group
    
class ValidRevision(formencode.FancyValidator):
    def _to_python(self, value, state):
        revision = Revision.find(value)
        if not revision: 
           raise formencode.Invalid(
                _("No revision with ID '%s' exists") % value,
                 value, state)
        return revision
        
class ValidComment(formencode.FancyValidator):
    def _to_python(self, value, state):
        comment = Comment.find(value)
        if not comment: 
           raise formencode.Invalid(
                _("No comment with ID '%s' exists") % value,
                 value, state)
        return comment

class ValidWatch(formencode.FancyValidator):
    def _to_python(self, value, state):
        watch = Watch.by_id(value)
        if not watch: 
           raise formencode.Invalid(
                _("No watchlist entry with ID '%s' exists") % value,
                 value, state)
        return watch
        
class ValidRef(formencode.FancyValidator):
    def _to_python(self, value, state):
        try:
            entity = refs.from_url(value)
            if not entity: 
                raise TypeError()
            return entity
        except: 
            raise formencode.Invalid(_("Invalid reference"), value, state)
        
class ExistingUserName(formencode.FancyValidator):
    def _to_python(self, value, state):
        user = User.find(value)
        if not user: 
           raise formencode.Invalid(
                _("No user with the user name '%s' exists") % value,
                value, state)
        return user

class ValidTagging(formencode.FancyValidator):
    def _to_python(self, value, state):
        tagging = Tagging.find(value)
        if not tagging: 
           raise formencode.Invalid(
                _("No tagging with ID '%s' exists") % value,
                 value, state)
        return tagging

