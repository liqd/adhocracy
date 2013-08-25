import logging
import hashlib
from pylons import config
from webhelpers import text
from pylons.i18n import _
from adhocracy.lib import mail, microblog

TWITTER_LENGTH = 140
TRUNCATE_EXT = '...'

log = logging.getLogger(__name__)


def log_sink(pipeline):
    for notification in pipeline:
        log.debug("Generated notification: %s" % notification)
        yield notification


def twitter_sink(pipeline):
    twitter_enabled = bool(config.get('adhocracy.twitter.username', ''))
    for notification in pipeline:
        user = notification.user
        if (twitter_enabled and user.twitter
           and notification.priority >= user.twitter.priority):
            notification.language_context()
            short_url = microblog.shorten_url(notification.link)
            remaining_length = TWITTER_LENGTH - \
                (1 + len(short_url) + len(TRUNCATE_EXT))
            tweet = text.truncate(notification.subject, remaining_length,
                                  TRUNCATE_EXT, False)
            tweet += ' ' + short_url

            log.debug("twitter DM to %s: %s" % (user.twitter.screen_name,
                                                tweet))
            api = microblog.create_default()
            api.PostDirectMessage(user.twitter.screen_name, tweet)
        else:
            yield notification


def mail_sink(pipeline):
    """
    Generates email-adress for comment-replies in the form of
    subscription.userid-commentid.security-token@domain.tld
    if the notification is about a new comment.
    HTML will be activated. If a user can not display HTML-emails
    the multipart/alternative plaintext-part will display the
    default notification.body. Otherwise an HTML-email is only
    a beautified version.
    This feature is not yet completed.
    """
    for notification in pipeline:
        if notification.user.is_email_activated() and \
                notification.priority >= notification.user.email_priority:
            notification.language_context()
            headers = {'X-Notification-Id': notification.id,
                       'X-Notification-Priority': str(notification.priority)}

            log.debug("mail to %s: %s" % (notification.user.email,
                                          notification.subject))

            notification_body = notification.body

            if str(notification.event.event) == "t_comment_create" or \
                    str(notification.event.event) == "n_comment_reply":

                secrets = config.get("adhocracy.crypto.secret")
                email_from = config.get("adhocracy.email.from")

                email_domain = email_from.rpartition("@")
                email_domain = email_domain[1] + email_domain[2]

                user_id = str(notification.user.id)

                comment_id = notification.link.split("#c")[-1]

                sec_token = user_id + comment_id + secrets
                sec_token = hashlib.sha1(sec_token).hexdigest()

                seq = (u" <subs.", user_id, u"-", comment_id, u".",
                        sec_token, email_domain, u">")
                reply_to = "".join(seq)
                reply_msg = _(u"\"Reply to leave a comment\"")
                reply_to = reply_msg + reply_to

                headers['In-Reply-To'] = reply_to
                headers['Reply-To'] = reply_to

                boundary = (u"_________________________________\r\n")

                notification_body = (_(u"Comment by replying to this email."
                u"\r\nWrite your answer above the upper line or under the"
                u" bottom line."
                u"\r\n\r\nYou can use the first line of your reply"
                u" to vote. Type vote 1 for a positive vote,"
                u" vote 0 for a neutral vote and vote -1 for a"
                u" negative vote.\r\n\r\n") + notification_body)
                # Mention images? (Don't work with markdown safe_mode yet)

                notification_body = boundary + (_(u"Hi %s,") %
                    notification.user.name +
                    u"\r\n%s\r\n\r\n" % notification_body +
                    _(u"Cheers,\r\n\r\n"
                    u"    the %s Team\r\n") %
                    config.get('adhocracy.site.name')) + u"\r\n" + boundary

                html = False
                # html deactivated due to email-comment parsing/voting
                decorate_body = False
            else:
                html = False

            mail.to_user(notification.user,
                    notification.subject,
                    notification_body,
                    headers=headers,
                    html=html,
                    decorate_body=decorate_body)
        else:
            yield notification
