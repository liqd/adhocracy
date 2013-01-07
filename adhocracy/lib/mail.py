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


def send(email_from, to_email, message):
    server = smtplib.SMTP(config.get('smtp_server', 'localhost'),
                          config.get('smtp_port', 25))
    #server.set_debuglevel(1)
    server.sendmail(email_from, [to_email], message)
    server.quit()


def to_mail(to_name, to_email, subject, body, headers={}, decorate_body=True):
    try:
        email_from = config.get('adhocracy.email.from')

        if decorate_body:
            body = (_(u"Hi %s,") % to_name +
                    u"\r\n\r\n%s\r\n\r\n" % body +
                    _(u"Cheers,\r\n\r\n"
                      u"    the %s Team\r\n") %
                    config.get('adhocracy.site.name'))

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
        send(email_from, to_email, msg.as_string())
    except Exception:
        log.exception("Sending mail failed.")


def to_user(to_user, subject, body, headers={}, decorate_body=True):
    return to_mail(to_user.name, to_user.email, subject, body, headers,
                   decorate_body=decorate_body)


def send_activation_link(user):
    url = h.base_url("/user/%s/activate?c=%s" % (user.user_name,
                                                     user.activation_code),
                         instance=None, absolute=True)
    body = _("this email is to check the email address you have provided. "
             "In order to confirm this email address, please open the link "
             "below in your browser:") + "\r\n\r\n  " + url
    to_user(user, _("Confirm your email address"), body)
