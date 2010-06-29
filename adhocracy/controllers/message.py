from pylons.i18n import _

from formencode import Invalid

from adhocracy.lib.base import *
import adhocracy.lib.text as text
import adhocracy.forms as forms
import adhocracy.i18n as i18n
import adhocracy.lib.logo as logo

import adhocracy.lib.instance as libinstance

log = logging.getLogger(__name__)


class MessageCreateForm(formencode.Schema):
    allow_extra_fields = True
    subject = validators.String(max=250, not_empty=True)
    body = validators.String(max=20000, min=2, not_empty=True)


class MessageController(BaseController):
    
    @RequireInstance
    def new(self, id, format='html', errors={}):
        c.page_user = get_entity_or_abort(model.User, id)
        require.user.message(c.page_user)
        html = render("/message/new.html")
        return htmlfill.render(html, defaults=request.params, 
                               errors=errors, force_defaults=False)
        
    
    @RequireInstance    
    def create(self, id, format='html'):
        c.page_user = get_entity_or_abort(model.User, id)
        require.user.message(c.page_user)
        try:
            self.form_result = MessageCreateForm().to_python(request.params)
        except Invalid, i:
            return self.new(id, errors=i.unpack_errors())
        
        c.body = self.form_result.get('body')
        c.subject = self.form_result.get('subject')
        message = render("/message/body.txt")
        headers = {}
        if c.user.is_email_activated():
            headers['Reply-To'] = c.user.email
        
        from adhocracy.lib.mail import to_user
        subject = _("[%s] Message from %s: %s") % (c.instance.label, c.user.name, c.subject)
        to_user(c.page_user, subject, message, headers=headers)
        
        h.flash(_("Your message has been sent. Thanks."))
        redirect(h.entity_url(c.page_user))   