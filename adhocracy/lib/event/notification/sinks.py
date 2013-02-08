import logging

from webhelpers import text

from adhocracy.lib import mail, microblog

TWITTER_LENGTH = 140
TRUNCATE_EXT = '...'

log = logging.getLogger(__name__)


def log_sink(pipeline):
    for notification in pipeline:
        log.debug("Generated notification: %s" % notification)
        yield notification


def twitter_sink(pipeline):
    for notification in pipeline:
        user = notification.user
        if user.twitter and (notification.priority >= user.twitter.priority):
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
    for notification in pipeline:
        if notification.user.is_email_activated() and \
                notification.priority >= notification.user.email_priority:
            notification.language_context()
            headers = {'X-Notification-Id': notification.id,
                       'X-Notification-Priority': str(notification.priority)}

            log.debug("mail to %s: %s" % (notification.user.email,
                                          notification.subject))
            mail.to_user(notification.user,
                         notification.subject,
                         notification.body,
                         headers=headers)

        else:
            yield notification
