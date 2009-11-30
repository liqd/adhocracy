from datetime import datetime, timedelta
import smtplib
import logging

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header

from pylons.i18n.translation import *
from pylons import session, config, request
import version

log = logging.getLogger(__name__)
ENCODING = 'utf-8'

def to_mail(to_name, to_email, subject, body, html_body=None, headers={}):
    email_from = config['adhocracy.email.from']
    smtp_server = config['smtp_server']
    
    print "XXX BODY ", body
    
    body = _(u"Hi %s,") % to_name \
         + u"\r\n\r\n%s\r\n\r\n" % body \
         + _(u"Cheers,\r\n\r\n    the Adhocracy Team\r\n")
    
    msg = MIMEText(body.encode(ENCODING), 'plain', ENCODING)
    if html_body:
        plain_part = MIMEText(body.encode(ENCODING), 
                              'plain', ENCODING)
        html_part = MIMEText(html_body.encode(ENCODING), 
                             'html', ENCODING)
        msg = MIMEMultipart('alternative')
        msg.attach(plain_part)
        msg.attach(html_part)
    
    for k, v in headers.items(): msg[k] = v
    
    subject = Header(subject.encode(ENCODING), ENCODING)
    msg['Subject'] = subject
    msg['From'] = _("Adhocracy <%s>") % email_from
    to = Header(u"%s <%s>" % (to_name, to_email), ENCODING)
    msg['To'] = to
    msg['X-Mailer'] = _("Adhocracy SMTP %s") % version.get_version()
    
    log.debug("MAIL\r\n" + msg.as_string())
         
    server = smtplib.SMTP(smtp_server)
    #server.set_debuglevel(1)
    server.sendmail(email_from, [to_email], msg.as_string())
    server.quit()
    
    
def to_user(to_user, subject, body, html_body=None, headers={}):
    return to_mail(to_user.name, to_user.email, subject, body, html_body, headers)