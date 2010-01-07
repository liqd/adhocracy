import urllib
from datetime import datetime

from pylons.i18n import _
from babel import Locale

import adhocracy.lib.text as text
from adhocracy.lib.base import *
import adhocracy.model.forms as forms
import adhocracy.lib.text.i18n as i18n
import adhocracy.lib.util as libutil
import adhocracy.lib.mail as libmail

log = logging.getLogger(__name__)
        
class UserCreateForm(formencode.Schema):
    allow_extra_fields = True
    user_name = formencode.All(validators.PlainText(),
                              forms.UniqueUsername())
    email = formencode.All(validators.Email(),
                           forms.UniqueEmail())
    password = validators.String(not_empty=True)
    password_confirm = validators.String(not_empty=True)
    chained_validators = [validators.FieldsMatch(
         'password', 'password_confirm')]
         
class UserEditForm(formencode.Schema):
    allow_extra_fields = True
    display_name = validators.String(not_empty=False)
    email = validators.Email(not_empty=True)
    locale = validators.String(not_empty=False)
    password = validators.String(not_empty=False)
    password_confirm = validators.String(not_empty=False)
    chained_validators = [validators.FieldsMatch(
        'password', 'password_confirm')]
    bio = validators.String(max=1000, min=0, not_empty=False)
    email_priority = validators.Int(min=0, max=6, not_empty=False, if_missing=4)
    twitter_priority = validators.Int(min=0, max=6, not_empty=False, if_missing=4)
    
class UserManageForm(formencode.Schema):
    allow_extra_fields = True
    group = forms.ValidGroup()

class UserResetApplyForm(formencode.Schema):
    allow_extra_fields = True
    email = validators.Email(not_empty=True)
    
class UserGroupmodForm(formencode.Schema):
    allow_extra_fields = True
    to_group = forms.ValidGroup()

class UserController(BaseController):
    
    @ActionProtector(has_permission("user.view"))
    def index(self):
        c.users = model.User.all(instance_filter=True if c.instance else False)
        c.users_pager = NamedPager('users', c.users, tiles.user.row,
                                    sorts={_("oldest"): sorting.entity_oldest,
                                           _("newest"): sorting.entity_newest,
                                           _("karma"): sorting.user_karma,
                                           _("activity"): sorting.user_activity,
                                           _("name"): sorting.user_name},
                                    default_sort=sorting.user_karma)
        return render("/user/index.html")
    
    @RequireInternalRequest(methods=['POST'])
    @validate(schema=UserCreateForm(), form="create", post_only=True)
    def create(self):
        if request.method == "POST":
            user = model.User(self.form_result.get("user_name"),
                              self.form_result.get("email"),
                              self.form_result.get("password"))
            user.locale = c.locale
            model.meta.Session.add(user)
            
            # the plan is to make this configurable via the instance preferences 
            # screen.             
            grp = model.Group.by_code(model.Group.CODE_DEFAULT)
            membership = model.Membership(user, None, grp)
            model.meta.Session.add(membership)
            model.meta.Session.commit()
            
            event.emit(event.T_USER_CREATE, user)
            
            if c.instance:
                session['came_from'] = "/instance/join/%s?%s" % (c.instance.key, h.url_token())
            login_page = render("/user/login.html")
            redirect_to("/user/perform_login?%s" % urllib.urlencode({
                    'login': self.form_result.get("user_name"),
                    'password': self.form_result.get("password")
                }))
        return render("/user/login.html")

    @RequireInternalRequest(methods=['POST'])
    @ActionProtector(has_permission("user.edit"))
    @validate(schema=UserEditForm(), form="edit", post_only=True)
    def edit(self, id):
        c.page_user = get_entity_or_abort(model.User, id, instance_filter=False)
        if not (c.page_user == c.user or h.has_permission("user.manage")): 
            abort(403, _("You're not authorized to change %s's settings.") % id)
        if request.method == "POST":
            if self.form_result.get("password"):
                c.page_user.password = self.form_result.get("password")
            c.page_user.display_name = self.form_result.get("display_name")
            c.page_user.bio = text.cleanup(self.form_result.get("bio"))
            c.page_user.email = self.form_result.get("email").lower()
            c.page_user.email_priority = self.form_result.get("email_priority")
            if c.page_user.twitter:
                c.page_user.twitter.priority = self.form_result.get("twitter_priority")
                model.meta.Session.add(c.page_user.twitter)
            locale = Locale(self.form_result.get("locale"))
            if locale and locale in i18n.LOCALES:
                c.page_user.locale = locale 
            model.meta.Session.add(c.page_user)
            model.meta.Session.commit()
            model.meta.Session.refresh(c.page_user)
            if c.page_user == c.user:
                event.emit(event.T_USER_EDIT, c.user)
            else:
                event.emit(event.T_USER_ADMIN_EDIT, c.page_user, admin=c.user)
            redirect_to("/user/%s" % str(c.page_user.user_name))
        return render("/user/edit.html")
    
    @validate(schema=UserResetApplyForm(), form="reset", post_only=True)
    def reset(self):
        if request.method == "POST":
            email = self.form_result.get('email').lower()
            query = model.meta.Session.query(model.User)
            query = query.filter(model.User.email==email)
            users = query.all()
            if not len(users):
                h.flash(_("There is no user registered with that email address."))
                return render("/user/reset_form.html")
            c.page_user = users[0]
            c.page_user.reset_code = libutil.random_token()
            model.meta.Session.add(c.page_user)
            model.meta.Session.commit()
            url = h.instance_url(None, path="/user/reset/%s?c=%s" % (c.page_user.user_name, c.page_user.reset_code))
            body = _("you have requested that your password be reset. In order to" 
                     +  " confirm the validity of your claim, please open the link below in your"
                     +  " browser:") + "\r\n\r\n  " + url 
            libmail.to_user(c.page_user, _("Reset your password"), body)
            return render("/user/reset_pending.html")
        return render("/user/reset_form.html")
    
    def reset_code(self, id):
        c.page_user = get_entity_or_abort(model.User, id, instance_filter=False)
        try:
            if c.page_user.reset_code != request.params.get('c', 'deadbeef'):
                h.flash(_("Invalid URL reset code."))
                redirect_to('/login')
             
            new_password = libutil.random_token()
            c.page_user.password = new_password
            model.meta.Session.add(c.page_user)
            model.meta.Session.commit()
            
            body = _("your password has been reset. It is now:") + "\r\n\r\n  " + new_password + "\r\n\r\n" 
            body += _("Please login and change the password in your user settings.")     
            libmail.to_user(c.page_user, _("Your new password"), body)     
            h.flash(_("Success. You have been sent an email with your new password."))    
        except Exception:
            h.flash(_("The reset code is invalid. Please repeat the password recovery procedure."))
        redirect_to('/login')
        
            
    @ActionProtector(has_permission("user.view"))
    def view(self, id, format='html'):
        c.page_user = get_entity_or_abort(model.User, id, instance_filter=False)
        bio = c.page_user.bio
        if not bio:
            bio = _("%(user)s is using Adhocracy, a direct democracy decision-making tool.") % {'user': c.page_user.name}
        
        description = h.text.truncate(text.meta_escape(bio), length=200, whole_word=True) 
        
        h.add_meta("description", description)
        h.add_meta("dc.title", text.meta_escape(c.page_user.name))
        h.add_meta("dc.date", c.page_user.access_time.strftime("%Y-%m-%d"))
        h.add_meta("dc.author", text.meta_escape(c.page_user.name))
                  
        h.add_rss(_("%(user)ss Activity") % {'user': c.page_user.name}, 
                  h.instance_url(None, "/user/%s.rss" % c.page_user.user_name))                         
            
        if c.instance and not c.page_user.is_member(c.instance):
            h.flash(_("%s is not a member of %s") % (c.page_user.name, c.instance.label))
        
        
        query = model.meta.Session.query(model.Event)
        query = query.filter(model.Event.user==c.page_user)
        query = query.order_by(model.Event.time.desc())
        query = query.limit(50)  
        c.events_pager = NamedPager('events', query.all(), tiles.event.list_item)
        if format == 'rss':
            return event.rss_feed(events, "%s Latest Actions" % c.page_user.name,
                                  h.instance_url(None, path='/user/%s' % c.page_user.user_name),
                                  description)
        c.tile = tiles.user.UserTile(c.page_user)
        
        return render("/user/view.html")
    
    def login(self):
        if 'came_from' in request.params:
            session['came_from'] = request.params.get('came_from')
            session.save()
        return render('/user/login.html')

    def perform_login(self):
        pass # managed by repoze.who

    def post_login(self):
        if c.user:
            if 'came_from' in session:
                url = str(session['came_from'])
                del session['came_from']
                session.save()
                redirect_to(url)
            #h.flash("Welcome back, %s" % c.user.user_name)
            redirect_to("/")
        else:
            return formencode.htmlfill.render(
                render("/user/login.html"), 
                errors = {"login": _("Invalid user name or password")})

    def logout(self):
        pass # managed by repoze.who

    def post_logout(self):
        redirect_to("/")
    
    @ActionProtector(has_permission("user.view"))    
    def autocomplete(self):
        try:
            prefix = unicode(request.params['q'])
            limit = int(request.params.get('limit', 5))
            users = model.User.complete(prefix, limit)
            result = ""
            for user in users:
                s = user.name
                if user.user_name != user.name:
                    s = "%s (%s)" % (user.user_name, s)
                result += "{s: '%s', k: '%s'}" % (s, user.user_name)
            return result
        except Exception, e:
            return ""
        
    @RequireInstance
    @ActionProtector(has_permission("user.view")) 
    def votes(self, id):
        c.page_user = get_entity_or_abort(model.User, id, instance_filter=False)
        decisions = democracy.Decision.for_user(c.page_user, c.instance)
            
        c.decisions_pager = NamedPager('decisions', decisions, tiles.decision.user_row, 
                                    sorts={_("oldest"): sorting.entity_oldest,
                                           _("newest"): sorting.entity_newest},
                                    default_sort=sorting.entity_newest)
        return render("/user/votes.html")
    
    @RequireInstance
    @ActionProtector(has_permission("delegation.view"))
    def delegations(self, id):
        c.page_user = get_entity_or_abort(model.User, id, instance_filter=False)
        scope_id = request.params.get('scope', None)
        c.dgbs = []
        if scope_id:
            c.scope = forms.ValidDelegateable().to_python(scope_id)
            c.dgbs = [c.scope] + c.scope.search_children(recurse=True)
        else:
            c.dgbs = model.Delegateable.all(instance=c.instance)  
        c.nodeClass = democracy.DelegationNode 
        
        return render("/user/delegations.html")
    
    @RequireInstance
    @RequireInternalRequest()
    @ActionProtector(has_permission("instance.admin"))
    @validate(schema=UserGroupmodForm(), form="create", post_only=False, on_get=True)
    def groupmod(self, id):
        c.page_user = get_entity_or_abort(model.User, id)
        to_group = self.form_result.get("to_group")
        if not to_group.code in [model.Group.CODE_OBSERVER, 
                                 model.Group.CODE_VOTER, 
                                 model.Group.CODE_SUPERVISOR]:
            h.flash("Cannot make %(user)s a member of %(group)s" % {
                        'user': user.name, 
                        'group': group.group_name})
            redirect_to("/user/%s" % str(c.page_user.user_name))
        
        had_vote = True if c.page_user._has_permission("vote.cast") else False
        
        for membership in c.page_user.memberships:
            if not membership.expire_time and membership.instance == c.instance:
                membership.expire_time = datetime.utcnow()
                model.meta.Session.add(membership)
        new_membership = model.Membership(c.page_user, c.instance, to_group)
        model.meta.Session.add(new_membership)
        model.meta.Session.commit()
        event.emit(event.T_INSTANCE_MEMBERSHIP_UPDATE, c.page_user, 
                   instance=c.instance, group=to_group.code, admin=c.user)
        
        if had_vote and not c.page_user._has_permission("vote.cast"):
            # user has lost voting privileges
            democracy.DelegationNode.detach(c.page_user, c.instance)
                
        redirect_to("/user/%s" % str(c.page_user.user_name))
    
    @RequireInstance
    @RequireInternalRequest()
    @ActionProtector(has_permission("instance.admin"))
    def kick(self, id):
        c.page_user = get_entity_or_abort(model.User, id)
        for membership in c.page_user.memberships:
            if not membership.expire_time and membership.instance == c.instance:
                membership.expire_time = datetime.utcnow()
                model.meta.Session.add(membership)
        model.meta.Session.commit()
        event.emit(event.T_INSTANCE_FORCE_LEAVE, c.page_user, instance=c.instance, 
                   admin=c.user)
        
        democracy.DelegationNode.detach(c.page_user, c.instance)
                        
        h.flash(_("%(user)s was removed from %(instance)s") % {
                                        'user': c.page_user.name, 
                                        'instance': c.instance.label})
        redirect_to("/user/%s" % str(c.page_user.user_name))
    