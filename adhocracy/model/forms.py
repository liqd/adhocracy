import re
import formencode
from formencode import validators, foreach

from pylons.i18n.translation import *

import meta
import refs
import user
import vote
import delegateable
import proposal
import issue
import group
import watch
import revision
import comment
import instance
import tagging

FORBIDDEN_NAMES = ["www", "static", "mail", "edit", "create", "settings", "join", "leave", 
                   "control", "test", "support", "page", "issue", "proposal"]

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
        if meta.Session.query(user.User.email).filter(user.User.email == email).all():
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
        if not instance.Instance.INSTANCE_KEY.match(value) or value in FORBIDDEN_NAMES:
            raise formencode.Invalid(
                _('The instance key is invalid'),
                value, state)
        if instance.Instance.find(value):
            raise formencode.Invalid(
                _('An instance with that key already exists'),
                value, state)
        return value

class ValidDelegateable(formencode.FancyValidator):
    def _to_python(self, value, state):
        dgb = delegateable.Delegateable.find(value)
        if not dgb: 
           raise formencode.Invalid(
                _("No entity with ID '%s' exists") % value,
                 value, state)
        return dgb

class ValidIssue(formencode.FancyValidator):
    def _to_python(self, value, state):
        iss = issue.Issue.find(value)
        if not iss: 
           raise formencode.Invalid(
                _("No issue with ID '%s' exists") % value,
                 value, state)
        return iss

class ValidProposal(formencode.FancyValidator):
    def _to_python(self, value, state):
        mot =  proposal.Proposal.find(value)
        if not mot: 
           raise formencode.Invalid(
                _("No proposal with ID '%s' exists") % value,
                 value, state)
        return mot

class ValidGroup(formencode.FancyValidator):
    def _to_python(self, value, state):
        grp =  group.Group.by_code(value)
        if not grp: 
           raise formencode.Invalid(
                _("No group with ID '%s' exists") % value,
                 value, state)
        return grp
    
class ValidRevision(formencode.FancyValidator):
    def _to_python(self, value, state):
        rev =  revision.Revision.find(value)
        if not rev: 
           raise formencode.Invalid(
                _("No revision with ID '%s' exists") % value,
                 value, state)
        return rev
        
class ValidComment(formencode.FancyValidator):
    def _to_python(self, value, state):
        cmt = comment.Comment.find(value)
        if not cmt: 
           raise formencode.Invalid(
                _("No comment with ID '%s' exists") % value,
                 value, state)
        return cmt

class ValidWatch(formencode.FancyValidator):
    def _to_python(self, value, state):
        wat = watch.Watch.by_id(value)
        if not wat: 
           raise formencode.Invalid(
                _("No watchlist entry with ID '%s' exists") % value,
                 value, state)
        return wat
        
class ValidRef(formencode.FancyValidator):
    def _to_python(self, value, state):
        entity = refs.from_url(value)
        if not entity: 
            raise formencode.Invalid(_("Invalid reference"), value, state)
        return entity
        
class ExistingUserName(formencode.FancyValidator):
    def _to_python(self, value, state):
        u =  user.User.find(value)
        if not u: 
           raise formencode.Invalid(
                _("No user with the user name '%s' exists") % value,
                value, state)
        return u

class ValidTagging(formencode.FancyValidator):
    def _to_python(self, value, state):
        taggin = tagging.Tagging.find_by_id(value)
        if not taggin: 
           raise formencode.Invalid(
                _("No tagging with ID '%s' exists") % value,
                 value, state)
        return taggin

