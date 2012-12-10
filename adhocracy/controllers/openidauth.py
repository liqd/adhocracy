import logging

import formencode
from formencode import validators

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect
from pylons.decorators import validate
from pylons.i18n import _
from webob.exc import HTTPFound


from openid.consumer.consumer import SUCCESS
from openid.extensions import sreg, ax

from adhocracy import forms, model
from adhocracy.lib import event, helpers as h
from adhocracy.lib.auth import login_user, require
from adhocracy.lib.auth.csrf import RequireInternalRequest
from adhocracy.lib.base import BaseController
from adhocracy.lib.openidstore import create_consumer
from adhocracy.lib.templating import render


log = logging.getLogger(__name__)


AX_MAIL_SCHEMA = u'http://schema.openid.net/contact/email'
AX_MEMBERSHIP_SCHEMA = u'http://schema.liqd.de/membership/signed/'


class OpenIDInitForm(formencode.Schema):
    openid = validators.OpenId(not_empty=False, if_empty=None,
                               if_missing=None, if_invalid=None)


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
        log the user in and redirect him to a sane place.
        """
        login_user(user, request)
        if c.instance and not user.is_member(c.instance):
            redirect(h.base_url("/instance/join/%s?%s" % (c.instance.key,
                                                    h.url_token())))
        redirect("/")

    def _failure(self, openid, message):
        """
        Abort an OpenID authenication attempt and return to login page,
        giving an error message at the openid field.
        """
        log.info("OpenID: %s - Error: %s" % (openid, message))
        if c.user:
            h.flash(message, 'error')
            return redirect(h.entity_url(c.user, member='edit'))
        else:
            loginhtml = render("/user/login.html")
            return formencode.htmlfill.render(loginhtml,
                                              defaults={'openid': openid},
                                              errors={'openid': message})

    def __before__(self):
        self.openid_session = session.get("openid_session", {})

    @validate(schema=OpenIDInitForm(), post_only=False, on_get=True)
    def init(self):
        self.consumer = create_consumer(self.openid_session)
        if not hasattr(self, 'form_result'):
            return self._failure('', _("Invalid input."))
        openid = self.form_result.get("openid")
        try:
            if not openid:
                raise ValueError(_("No OpenID given!"))
            authrequest = self.consumer.begin(openid)

            if not c.user and not model.OpenID.find(openid):
                axreq = ax.FetchRequest(h.base_url('/openid/update',
                                                   absolute=True))
                axreq.add(ax.AttrInfo(AX_MAIL_SCHEMA, alias="email",
                                      required=True))
                authrequest.addExtension(axreq)
                sreq = sreg.SRegRequest(required=['nickname'],
                                        optional=['email'])
                authrequest.addExtension(sreq)

            redirecturl = authrequest.redirectURL(
                h.base_url('/', absolute=True),
                return_to=h.base_url('/openid/verify', absolute=True),
                immediate=False)
            session['openid_session'] = self.openid_session
            session.save()
            return redirect(redirecturl)
        except HTTPFound:
            raise
        except Exception, e:
            log.exception(e)
            return self._failure(openid, str(e))

    def connect(self):
        require.user.edit(c.user)
        if not c.user:
            h.flash(_("No OpenID was entered."), 'warning')
            redirect("/login")
        return render("/openid/connect.html")

    @RequireInternalRequest()
    def revoke(self):
        require.user.edit(c.user)
        id = request.params.get('id')
        openid = model.OpenID.by_id(id)
        if not openid:
            abort(404, _("No OpenID with ID '%s' exists.") % id)
        page_user = openid.user
        if not (page_user == c.user or h.has_permission("user.manage")):
            abort(403,
                  _("You're not authorized to change %s's settings.") % id)
        openid.delete()
        model.meta.Session.commit()
        redirect(h.entity_url(c.user, member='edit'))

    def verify(self):
        self.consumer = create_consumer(self.openid_session)
        info = self.consumer.complete(request.params,
                                      h.base_url('/openid/verify',
                                                 absolute=True))
        if not info.status == SUCCESS:
            return self._failure(info.identity_url, _("OpenID login failed."))
        email = None
        user_name = None
        # evaluate Simple Registration Extension data
        srep = sreg.SRegResponse.fromSuccessResponse(info)
        if srep:
            if srep.get('nickname'):
                user_name = srep.get('nickname').strip()
            if srep.get('email'):
                email = srep.get('email')
        # evaluate Attribute Exchange data
        # TBD: AXSCHEMA friendlyName
        # TBD: SignedMembership
        axrep = ax.FetchResponse.fromSuccessResponse(info)
        if axrep:
            try:
                email = axrep.getSingle(AX_MAIL_SCHEMA) or email
            except ValueError:
                email = axrep.get(AX_MAIL_SCHEMA)[0]
            except KeyError:
                email = email

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
                redirect(h.entity_url(c.user, member='edit'))
            else:
                try:
                    forms.UniqueUsername(not_empty=True).to_python(user_name)
                except:
                    session['openid_req'] = (info.identity_url, user_name,
                                             email)
                    session.save()
                    redirect('/openid/username')
                user = self._create(user_name, email, info.identity_url)
                self._login(user)
        return self._failure(info.identity_url,
                             _("Justin Case has entered the room."))

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
                c.user_name = forms.UniqueUsername(
                    not_empty=True).to_python(c.user_name)
                if c.user_name:
                    user = self._create(c.user_name, email, openid)
                    del session['openid_req']
                    self._login(user)
            return render('/openid/username.html')
        else:
            redirect('/register')

    def xrds(self):
        response.headers['Content-Type'] = ("application/xrds+xml; "
                                            "charset=utf-8")
        return render('/openid/xrds.xml')
