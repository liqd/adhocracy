from datetime import datetime, timedelta
import sha
import smtplib

from pylons.i18n.translation import *
from pylons import session, config, request

def to_mail(to_name, to_email, subject, body):
    email_from = config['adhocracy.email.from']
    smtp_server = config['smtp_server']
    
    header = "From: Adhocracy <%s>\r\n" % email_from \
           + "To: %s <%s>\r\n" % (to_name, to_email) \
           + "Date: %s\r\n" % datetime.utcnow().ctime() \
           + "X-Mailer: adhocracy\r\n" \
           + "Subject: %s\r\n\r\n" % subject 
    body = _("Hi %s,") % to_name \
         + "\r\n\r\n%s\r\n\r\n" % body \
         + _("Cheers,\r\n\r\n    the Adhocracy Team\r\n")
         
    server = smtplib.SMTP(smtp_server)
    #server.set_debuglevel(1)
    server.sendmail(email_from, [to_email], header + body)
    server.quit()
    
def to_user(to_user, subject, body):
    return to_mail(to_user.name, to_user.email, subject, body)