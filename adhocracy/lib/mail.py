from datetime import datetime, timedelta
import smtplib
import logging
from time import time

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
import email

from pylons.i18n.translation import *
from pylons import session, config, request
import version

import helpers as h

log = logging.getLogger(__name__)
ENCODING = 'utf-8'

def to_mail(to_name, to_email, subject, body, headers={}):
    try:
        email_from = config.get('adhocracy.email.from')
        
        body = _(u"Hi %s,") % to_name \
             + u"\r\n\r\n%s\r\n\r\n" % body \
             + _(u"Cheers,\r\n\r\n    the %s Team\r\n") % config.get('adhocracy.site.name')
        
        msg = MIMEText(body.encode(ENCODING), 'plain', ENCODING)
        
        for k, v in headers.items(): msg[k] = v
        
        subject = Header(subject.encode(ENCODING), ENCODING)
        msg['Subject'] = subject
        msg['From'] = _("%s <%s>") % (config.get('adhocracy.site.name'), email_from)
        to = Header(u"%s <%s>" % (to_name, to_email), ENCODING)
        msg['To'] = to
        msg['Date'] = email.Utils.formatdate(time())
        msg['X-Mailer'] = _("Adhocracy SMTP %s") % version.get_version()
        
        #log.debug("MAIL\r\n" + msg.as_string())
             
        server = smtplib.SMTP(config.get('smtp_server', 'localhost'))
        #server.set_debuglevel(1)
        server.sendmail(email_from, [to_email], msg.as_string())
        server.quit()
    except Exception:
        log.exception("Sending mail failed.")
    
    
def to_user(to_user, subject, body, headers={}):
    return to_mail(to_user.name, to_user.email, subject, body, headers)

def send_activation_link(user):
    url = h.base_url(None, path="/user/%s/activate?c=%s" % (user.user_name, user.activation_code))
    body = _("this email is to check the email address you have provided. In order to" 
             + " confirm this email address, please open the link below in your"
             + " browser:") + "\r\n\r\n  " + url 
    to_user(user, _("Confirm your email address"), body)
