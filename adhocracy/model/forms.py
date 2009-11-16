import re
import formencode
from formencode import validators, foreach

from pylons.i18n.translation import *

import meta
import user
import vote
import delegateable
import motion
import category
import issue
import group
import revision
import comment
import instance

FORBIDDEN_NAMES = ["www", "static", "mail", "edit", "create", "settings", "join", "leave", 
                   "control", "test", "support"]

VALIDUSER = re.compile("^[a-zA-Z0-9_\-]{3,255}$")
class UniqueUsername(formencode.FancyValidator):
    def _to_python(self, value, state):
        if not value:
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

class ValidCategory(formencode.FancyValidator):
    def _to_python(self, value, state):
        cat =  category.Category.find(value)
        if not cat: 
           raise formencode.Invalid(
                _("No category with ID '%s' exists") % value,
                 value, state)
        return cat

class ValidIssue(formencode.FancyValidator):
    def _to_python(self, value, state):
        iss = issue.Issue.find(value)
        if not iss: 
           raise formencode.Invalid(
                _("No issue with ID '%s' exists") % value,
                 value, state)
        return iss

class ValidMotion(formencode.FancyValidator):
    def _to_python(self, value, state):
        mot =  motion.Motion.find(value)
        if not mot: 
           raise formencode.Invalid(
                _("No motion with ID '%s' exists") % value,
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
    
class ValidMotionState(formencode.FancyValidator):
    def _to_python(self, value, state):
        if not value in motion.Motion.STATES: 
           raise formencode.Invalid(
                _("'%s' is not a valid motion state."),
                 value, state)
        return value
        
class ExistingUserName(formencode.FancyValidator):
    def _to_python(self, value, state):
        u =  user.User.find(value)
        if not u: 
           raise formencode.Invalid(
                _("No user with the user name '%s' exists") % value,
                value, state)
        return u

    
class EditorAddForm(formencode.Schema):
    allow_extra_fields = True
    editor = ExistingUserName(not_empty=True)
    motion = ValidMotion(not_emtpy=True)

class EditorRemoveForm(formencode.Schema):
    allow_extra_fields = True
    editor = ExistingUserName(not_empty=True)
    motion = ValidMotion(not_emtpy=True)
    
class VoteCastForm(formencode.Schema):
    allow_extra_fields = True
    orientation = validators.Int(min=vote.Vote.NAY, max=vote.Vote.AYE, not_empty=True)
    
class CategoryCreateForm(formencode.Schema):
    allow_extra_fields = True
    label = validators.String(max=255, min=4, not_empty=True)
    description = validators.String(max=1000, if_empty=None, not_empty=False)
    categories = ValidCategory(not_empty=True)
    
class CategoryEditForm(formencode.Schema):
    allow_extra_fields = True
    label = validators.String(max=255, min=4, not_empty=True)
    description = validators.String(max=1000, if_empty=None, not_empty=False)
    categories = ValidCategory(not_emtpy=True)
    
class DelegationCreateForm(formencode.Schema):
    allow_extra_fields = True
    agent = ExistingUserName()
    
class AdminUpdateMembershipForm(formencode.Schema):
    allow_extra_fields = True
    user = ExistingUserName()
    to_group = ValidGroup()

class AdminForceLeaveForm(formencode.Schema):
    allow_extra_fields = True
    user = ExistingUserName()
    
class EventPanelForm(formencode.Schema):
    allow_extra_fields = True
    event_page = validators.Int(if_missing=1, not_empty=False)
    event_count = validators.Int(if_missing=None, if_invalid=None, max=100, not_empty=False)