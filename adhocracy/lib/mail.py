import email
from email.header import Header
from email.mime.text import MIMEText
import logging
import smtplib
from time import time

from pylons.i18n import _
from pylons import config

from adhocracy.lib import helpers as h, version

log = logging.getLogger(__name__)
ENCODING = 'utf-8'


def to_mail(to_name, to_email, subject, body, headers={}):
    try:
        email_from = config.get('adhocracy.email.from')

        body = (_(u"Hi %s,") % to_name +
                u"\r\n\r\n%s\r\n\r\n" % body +
                _(u"Cheers,\r\n\r\n"
                  u"    the %s Team\r\n") % config.get('adhocracy.site.name'))

        msg = MIMEText(body.encode(ENCODING), 'plain', ENCODING)

        for k, v in headers.items():
            msg[k] = v

        subject = Header(subject.encode(ENCODING), ENCODING)
        msg['Subject'] = subject
        msg['From'] = _("%s <%s>") % (config.get('adhocracy.site.name'),
                                      email_from)
        to = Header(u"%s <%s>" % (to_name, to_email), ENCODING)
        msg['To'] = to
        msg['Date'] = email.Utils.formatdate(time())
        msg['X-Mailer'] = "Adhocracy SMTP %s" % version.get_version()

        #log.debug("MAIL\r\n" + msg.as_string())

        server = smtplib.SMTP(config.get('smtp_server', 'localhost'),
                              config.get('smtp_port', 25))
        #server.set_debuglevel(1)
        server.sendmail(email_from, [to_email], msg.as_string())
        server.quit()
    except Exception:
        log.exception("Sending mail failed.")


def to_user(to_user, subject, body, headers={}):
    return to_mail(to_user.name, to_user.email, subject, body, headers)


def send_activation_link(user):
    url = h.base_url(None,
                     path="/user/%s/activate?c=%s" % (user.user_name,
                                                      user.activation_code))
    body = _("this email is to check the email address you have provided. "
             "In order to confirm this email address, please open the link "
             "below in your browser:") + "\r\n\r\n  " + url
    to_user(user, _("Confirm your email address"), body)
