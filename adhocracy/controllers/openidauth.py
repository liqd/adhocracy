import logging
from datetime import datetime

from pylons.i18n import _
import formencode

from openid.consumer.consumer import Consumer, SUCCESS, DiscoveryFailure
from openid.extensions import sreg, ax

from adhocracy.lib.base import *
from adhocracy.lib.openidstore import create_consumer
import adhocracy.lib.util as util
import adhocracy.model.forms as forms

log = logging.getLogger(__name__)


AX_MAIL_SCHEMA = u'http://schema.openid.net/contact/email'
AX_MEMBERSHIP_SCHEMA = u'http://schema.liqd.de/membership/signed/'

class OpenIDInitForm(formencode.Schema):
    openid = validators.OpenId(not_empty=False, if_empty=None)
    
class OpenIDUsernameForm(formencode.Schema):
    login = formencode.All(validators.PlainText(),
                           forms.UniqueUsername())

class OpenidauthController(BaseController):
    
                
    def _create(self, user_name, email, identity):
        """
        Create a user based on data gathered from OpenID
        """
        user = model.User.create(user_name, email, locale=c.locale, 
                                 openid_identity=identity)
        # trust provided email:
        user.activation_code = None
        model.meta.Session.commit()
        event.emit(event.T_USER_CREATE, user)
        return user

    def _login(self, user):
        """
        Raw login giving severe headaches to repoze.who, repoze.what and any
        bystanding squirrels. 
        """
        identity = {
            'userdata': '',
            'repoze.who.userid': str(user.user_name),
            'timestamp': int(datetime.utcnow().strftime("%s")),
            'user': user,
                    }
        
        # set up repoze.what
        authorization_md = request.environ['repoze.who.plugins']['authorization_md']
        authorization_md.add_metadata(request.environ, identity)
                  
        auth_tkt = request.environ['repoze.who.plugins']['auth_tkt']
        header = auth_tkt.remember(request.environ, identity)
        response.headerlist.extend(header)
                
        if c.instance and not user.is_member(c.instance):
            redirect_to(h.instance_url(c.instance, 
                        path="/instance/join/%s?%s" % (c.instance.key, 
                                                       h.url_token())))
        redirect_to("/")        
            
    def _failure(self, openid, message):
        """
        Abort an OpenID authenication attempt and return to login page, 
        giving an error message at the openid field.
        """
        log.info("OpenID: %s - Error: %s" % (openid, message))
        if c.user:
            h.flash(message)
            return redirect_to("/user/%s/edit" % str(c.user.user_name))
        else:
            loginhtml = render("/user/login.html")
            return formencode.htmlfill.render(loginhtml, 
                defaults = {'openid': openid}, 
                errors = {'openid': message})
    

    def __before__(self):
        self.openid_session = session.get("openid_session", {})
    
    @validate(schema=OpenIDInitForm(), form="foo", post_only=False, on_get=True)
    def init(self):
        self.consumer = create_consumer(self.openid_session)
        openid = self.form_result.get("openid")
        try:
            if not openid: raise ValueError(_("No OpenID given!"))
            authrequest = self.consumer.begin(openid)
        except Exception, e:
            return self._failure(openid, str(e))
        
        if not c.user and not model.OpenID.by_id(openid):
            axreq = ax.FetchRequest(h.instance_url(c.instance, path='/openid/update'))
            axreq.add(ax.AttrInfo(AX_MAIL_SCHEMA, alias="email", required=True))
            authrequest.addExtension(axreq)

            sreq = sreg.SRegRequest(required=['nickname'], optional=['email'])
            authrequest.addExtension(sreq)    
        
        redirecturl = authrequest.redirectURL(h.instance_url(c.instance, path='/'), 
                                    return_to=h.instance_url(c.instance, path='/openid/verify'), 
                                    immediate=False)
        session['openid_session'] = self.openid_session
        session.save()
        return redirect_to(redirecturl)
    
    @ActionProtector(has_permission("user.edit"))
    def connect(self):
        if not c.user:
            h.flash(_("No OpenID was entered."))
            redirect_to("/login")
        return render("/openid/connect.html")   
    
    @RequireInternalRequest()
    @ActionProtector(has_permission("user.edit"))
    def revoke(self, id):
        openid = model.OpenID.by_id(id)
        if not openid:
            abort(404, _("No OpenID with ID '%s' exists.") % id)
        page_user = openid.user
        if not (page_user == c.user or h.has_permission("user.manage")): 
            abort(403, _("You're not authorized to change %s's settings.") % id)
        openid.delete()
        model.meta.Session.commit()
        return redirect_to("/user/%s/edit" % str(page_user.user_name))

    def verify(self):
        self.consumer = create_consumer(self.openid_session)
        info = self.consumer.complete(request.params, h.instance_url(c.instance, path='/openid/verify'))
        if not info.status == SUCCESS:
            return self._failure(info.identity_url, _("OpenID login failed."))
        
        email = None
        user_name = None
            
        # evaluate Simple Registration Extension data
        srep = sreg.SRegResponse.fromSuccessResponse(info)
        if srep:
            user_name = srep.get('nickname').strip()
            if srep.get('email'):
                email = srep.get('email')
                    
        # evaluate Attribute Exchange data        
        # TBD: AXSCHEMA friendlyName 
        # TBD: SignedMembership
        axrep = ax.FetchResponse.fromSuccessResponse(info)
        if axrep:
            args = axrep.getExtensionArgs()
            if args.get('type.ext0') == AX_MAIL_SCHEMA:
                email = args.get('value.ext0.1')
            
        if 'openid_session' in session:
            del session['openid_session']
                
        oid = model.OpenID.find(info.identity_url)
        if oid:
            if c.user:
                if oid.user == c.user:
                    return self._failure(info.identity_url, 
                        _("You have already claimed this OpenID."))
                else:
                    return self._failure(info.identity_url,
                        _("OpenID %s already belongs to %s.") 
                        % (info.identity_url, oid.user.name))
            else: 
                self._login(oid.user)
                # returns
        else:
            if c.user:
                oid = model.OpenID(unicode(info.identity_url), c.user)
                model.meta.Session.add(oid)
                model.meta.Session.commit()
                redirect_to("/user/%s/edit" % str(c.user.user_name))
            else:
                try:
                    forms.UniqueUsername(not_empty=True).to_python(user_name)
                except:
                    session['openid_req'] = (info.identity_url, user_name, email)
                    session.save()
                    redirect_to('/openid/username')
                user = self._create(user_name, email, info.identity_url)
                self._login(user)
                    
        return self._failure(info.identity_url, _("Justin Case has entered the room."))

    @validate(schema=OpenIDUsernameForm(), form="username", post_only=True)
    def username(self):
        """
        Called when the nickname proposed by the OpenID identity provider is 
        unavailable locally. 
        """
        if 'openid_req' in session:
            (openid, c.user_name, email) = session['openid_req']
            if request.method == "POST":
                c.user_name = self.form_result.get('login')
                c.user_name = forms.UniqueUsername(not_empty=True).to_python(c.user_name)
                if c.user_name:
                    user = self._create(c.user_name, email, openid)
                    del session['openid_req']
                    self._login(user)
            return render('/openid/username.html')
        else:
            redirect_to('/register')
