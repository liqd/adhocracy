import logging 

import webhelpers.text as text

from ... import mail
from ... import microblog

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
            tweet = text.truncate(notification.subject, 130, '...', True)
            try:
                api = microblog.create_api()
                api.PostDirectMessage(user.twitter.screen_name, tweet)
            except Exception, e:
                log.warn(e)
                yield notification
        else:
            yield notification

def mail_sink(pipeline):
    for notification in pipeline:
        if notification.priority >= notification.user.email_priority:
            notification.language_context() 
            headers = {'X-Notification-Id': notification.id,
                       'X-Priority': str(notification.priority)}
            try:
                mail.to_user(notification.user, 
                         notification.subject, 
                         notification.body, 
                         headers=headers)
            except Exception, e:
                #import traceback
                #traceback.print_exc()
                log.warn(e)
                yield notification
        else:
            yield notification