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
         
class UserUpdateForm(formencode.Schema):
    allow_extra_fields = True
    display_name = validators.String(not_empty=False)
    email = validators.Email(not_empty=True)
    locale = validators.String(not_empty=False)
    password = validators.String(not_empty=False)
    password_confirm = validators.String(not_empty=False)
    chained_validators = [validators.FieldsMatch(
        'password', 'password_confirm')]
    bio = validators.String(max=1000, min=0, not_empty=False)
    email_priority = validators.Int(min=0, max=6, not_empty=False, if_missing=3)
    twitter_priority = validators.Int(min=0, max=6, not_empty=False, if_missing=3)
    
class UserCodeForm(formencode.Schema):
    allow_extra_fields = True
    c = validators.String(not_empty=False)
    
class UserManageForm(formencode.Schema):
    allow_extra_fields = True
    group = forms.ValidGroup()

class UserResetApplyForm(formencode.Schema):
    allow_extra_fields = True
    email = validators.Email(not_empty=True)
    
class UserGroupmodForm(formencode.Schema):
    allow_extra_fields = True
    to_group = forms.ValidGroup()
    
class UserFilterForm(formencode.Schema):
    allow_extra_fields = True
    users_q = validators.String(max=255, not_empty=False, if_empty=None, if_missing=None)

class UserController(BaseController):
    
    @ActionProtector(has_permission("user.view"))
    @validate(schema=UserFilterForm(), post_only=False, on_get=True)
    def index(self, format='html'):
        query = self.form_result.get('users_q')
        if query:
            c.users = libsearch.query.run(query + "*", entity_type=model.User)
            if c.instance:
                c.users = filter(lambda u: u.is_member(c.instance), c.users)
        else:
            c.users = model.User.all(instance=c.instance if c.instance else None)
        
        if format == 'json':
            return render_json(c.users)
        
        sorts={_("oldest"): sorting.entity_oldest,
               _("newest"): sorting.entity_newest,
               _("activity"): sorting.user_activity,
               _("name"): sorting.user_name}
        if query:
            sorts[_("relevance")] = sorting.entity_stable
                
        c.users_pager = NamedPager('users', c.users, tiles.user.row, sorts=sorts,
                                   default_sort=sorting.entity_stable if query else sorting.user_activity)
        return render("/user/index.html")
    
    
    def new(self):
        return render("/user/login.html")
    
    
    @RequireInternalRequest(methods=['POST'])
    @validate(schema=UserCreateForm(), form="new", post_only=True)
    def create(self):
        user = model.User.create(self.form_result.get("user_name"), 
                                 self.form_result.get("email").lower(), 
                                 password=self.form_result.get("password"), 
                                 locale=c.locale)
        model.meta.Session.commit()
            
        event.emit(event.T_USER_CREATE, user)
        libmail.send_activation_link(user)
        
        if c.instance:
            session['came_from'] = "/instance/join/%s?%s" % (c.instance.key, h.url_token())
        redirect_to("/user/perform_login?%s" % urllib.urlencode({
                    'login': self.form_result.get("user_name"),
                    'password': self.form_result.get("password")
                }))
    
    
    @ActionProtector(has_permission("user.edit"))
    def edit(self, id):
        c.page_user = self._get_user_for_edit(id)
        return render("/user/edit.html")
    
    
    @RequireInternalRequest(methods=['POST'])
    @ActionProtector(has_permission("user.edit"))
    @validate(schema=UserUpdateForm(), form="edit", post_only=True)
    def update(self, id):
        c.page_user = self._get_user_for_edit(id)
        if self.form_result.get("password"):
            c.page_user.password = self.form_result.get("password")
        c.page_user.display_name = self.form_result.get("display_name")
        c.page_user.bio = text.cleanup(self.form_result.get("bio"))
        email = self.form_result.get("email").lower()
        email_changed = email != c.page_user.email
        c.page_user.email = email
        c.page_user.email_priority = self.form_result.get("email_priority")
        if c.page_user.twitter:
            c.page_user.twitter.priority = self.form_result.get("twitter_priority")
            model.meta.Session.add(c.page_user.twitter)
        locale = Locale(self.form_result.get("locale"))
        if locale and locale in i18n.LOCALES:
            c.page_user.locale = locale 
        model.meta.Session.add(c.page_user)
        model.meta.Session.commit()
        
        if email_changed:
            libmail.send_activation_link(c.page_user)       
        
        if c.page_user == c.user:
            event.emit(event.T_USER_EDIT, c.user)
        else:
            event.emit(event.T_USER_ADMIN_EDIT, c.page_user, admin=c.user)
        redirect_to("/user/%s" % str(c.page_user.user_name))
    
    
    def reset_form(self):
        return render("/user/reset_form.html")
    
    
    @validate(schema=UserResetApplyForm(), form="reset", post_only=True)
    def reset_request(self):
        c.page_user = model.User.find_by_email(self.form_result.get('email'))
        if c.page_user is None:
            msg = _("There is no user registered with that email address.")
            return htmlfill.render(self.reset_form(), errors=dict(email=msg))
        
        c.page_user.reset_code = libutil.random_token()
        model.meta.Session.add(c.page_user)
        model.meta.Session.commit()
        url = h.instance_url(None, path="/user/%s/reset?c=%s" % (c.page_user.user_name, c.page_user.reset_code))
        body = _("you have requested that your password be reset. In order to" 
                 +  " confirm the validity of your claim, please open the link below in your"
                 +  " browser:") + "\r\n\r\n  " + url 
        libmail.to_user(c.page_user, _("Reset your password"), body)
        return render("/user/reset_pending.html")
    
    
    @validate(schema=UserCodeForm(), form="reset_form", post_only=False, on_get=True)
    def reset(self, id):
        c.page_user = get_entity_or_abort(model.User, id, instance_filter=False)
        try:
            if c.page_user.reset_code != self.form_result.get('c'):
                raise ValueError()
             
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
    
    
    @ActionProtector(has_permission("user.edit"))
    @validate(schema=UserCodeForm(), form="edit", post_only=False, on_get=True)
    def activate(self, id):
        c.page_user = self._get_user_for_edit(id)
        try:
            if c.page_user.activation_code != self.form_result.get('c'):
                raise ValueError()
            c.page_user.activation_code = None
            model.meta.Session.commit()
            h.flash(_("Your email has been confirmed."))
        except Exception:
            log.exception("Invalid activation code")
            h.flash(_("The activation code is invalid. Please have it resent."))
        redirect_to("/user/%s/edit" % str(c.page_user.user_name))
    
    
    @RequireInternalRequest()
    @ActionProtector(has_permission("user.edit"))
    def resend(self, id):
        c.page_user = self._get_user_for_edit(id)
        libmail.send_activation_link(c.page_user)
        h.flash(_("The activation link has been re-sent to your email address."))
        redirect_to("/user/%s/edit" % str(c.page_user.user_name))
    
     
    @ActionProtector(has_permission("user.view"))
    def show(self, id, format='html'):
        c.page_user = get_entity_or_abort(model.User, id, instance_filter=False)
        
        if format == 'json':
            return render_json(c.page_user)
        
        query = model.meta.Session.query(model.Event)
        query = query.filter(model.Event.user==c.page_user)
        query = query.order_by(model.Event.time.desc())
        query = query.limit(50)  
        if format == 'rss':
            return event.rss_feed(query.all(), "%s Latest Actions" % c.page_user.name,
                                  h.instance_url(None, path='/user/%s' % c.page_user.user_name),
                                  description)
        c.events_pager = NamedPager('events', query.all(), tiles.event.row, count=10)
        c.tile = tiles.user.UserTile(c.page_user)
        
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
        
        return render("/user/show.html")
    
    
    @ActionProtector(has_permission("user.delete"))
    def delete(self, id):
        self.not_implemented()
    
    
    def login(self):
        session['came_from'] = request.params.get('came_from')
        session.save()
        return render('/user/login.html')
    
    
    def perform_login(self): pass # managed by repoze.who
    
    
    def post_login(self):
        if c.user:
            url = '/'
            if 'came_from' in session:
                session.get('came_from')
                del session['came_from']
                session.save()
            redirect_to(str(url))
        else:
            return formencode.htmlfill.render(
                render("/user/login.html"), 
                errors = {"login": _("Invalid user name or password")})
    
    
    def logout(self): pass # managed by repoze.who

    def post_logout(self):
        redirect_to("/")
    
    
    @ActionProtector(has_permission("user.view"))    
    def complete(self):
        prefix = unicode(request.params.get('q', ''))
        users = model.User.complete(prefix, 15)
        results = []
        for user in users:
            if user == c.user: continue
            display = "%s (%s)" % (user.user_name, user.name) if \
                      user.display_name else user.name
            results.append(dict(display=display, user=user.user_name))
        return render_json(results)
    
        
    @RequireInstance
    @ActionProtector(has_permission("user.view")) 
    def votes(self, id, format='html'):
        c.page_user = get_entity_or_abort(model.User, id, instance_filter=False)
        decisions = democracy.Decision.for_user(c.page_user, c.instance)
        
        if format == 'json':
            return render_json(list(decisions))
        
        c.decisions_pager = NamedPager('decisions', decisions, tiles.decision.user_row, 
                                    sorts={_("oldest"): sorting.entity_oldest,
                                           _("newest"): sorting.entity_newest},
                                    default_sort=sorting.entity_newest)
        return render("/user/votes.html")
    
    
    @RequireInstance
    @ActionProtector(has_permission("delegation.view"))
    def delegations(self, id, format='html'):
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
    @validate(schema=UserGroupmodForm(), form="edit", post_only=False, on_get=True)
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
        
        had_vote = c.page_user._has_permission("vote.cast")
        
        for membership in c.page_user.memberships:
            if not membership.expire_time and membership.instance == c.instance:
                membership.expire_time = datetime.utcnow()
                model.meta.Session.add(membership)
        new_membership = model.Membership(c.page_user, c.instance, to_group)
        model.meta.Session.add(new_membership)
        model.meta.Session.commit()
        event.emit(event.T_INSTANCE_MEMBERSHIP_UPDATE, c.page_user, 
                   instance=c.instance, group=to_group, admin=c.user)
        
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
    
    
    @ActionProtector(has_permission("user.view"))
    @validate(schema=UserFilterForm(), post_only=False, on_get=True)
    def filter(self):
        query = self.form_result.get('users_q')
        users = libsearch.query.run(query + "*", entity_type=model.User)
        if c.instance:
            users = filter(lambda u: u.is_member(c.instance), users)
        c.users_pager = NamedPager('users', users, tiles.user.row,
                                    sorts={_("oldest"): sorting.entity_oldest,
                                           _("newest"): sorting.entity_newest,
                                           _("activity"): sorting.user_activity,
                                           _("relevance"): sorting.entity_stable,
                                           _("name"): sorting.user_name},
                                    default_sort=sorting.entity_stable)
        return c.users_pager.here()
    
    
    def _get_user_for_edit(self, id):
        user = get_entity_or_abort(model.User, id, instance_filter=False)
        if not (user == c.user or h.has_permission("user.manage")): 
            abort(403, _("You're not authorized to change %s's settings.") % id)
        return user
