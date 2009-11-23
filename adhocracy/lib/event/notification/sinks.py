import logging 

from ... import mail

log = logging.getLogger(__name__)

def log_sink(pipeline):
    for notification in pipeline:
        log.debug("Generated notification: %s" % notification)
        yield notification

def mail_sink(pipeline):
    for notification in pipeline:
        headers = {'X-Notification-Id': notification.id,
                   'X-Priority': str(notification.priority)}
        mail.to_user(notification.user, 
                     notification.subject, 
                     notification.plain_body, 
                     html_body=notification.html_body,
                     headers=headers)
        yield notification