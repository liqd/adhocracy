import logging
from amqp import has_queue, post_message, consume
from update import handle_update, post_update, UPDATE_SERVICE

from adhocracy import model
log = logging.getLogger(__name__)

MINUTE = 'minute'
HOURLY = 'hourly'
DAILY = 'daily'


def minute():
    post_message(MINUTE, '')


def hourly():
    post_message(HOURLY, '')


def daily():
    post_message(DAILY, '')


def update_solr_for_all_user():
    '''
    Reindex all users in solr. Mainly to update their
    activity measurements.
    '''
    user_query = model.User.all_q()
    for user in user_query:
        post_update(user, model.update.UPDATE)


def update_solr_for_all_instances():
    '''
    Reindex all instances in solr. Mainly to update their
    activity measurements.
    '''
    instance_query = model.Instance.all_q()
    for instance in instance_query:
        post_update(instance, model.update.UPDATE)


# TODO: Inversion of control
def dispatch():
    import adhocracy.model as model
    from adhocracy.lib import event
    from adhocracy.lib import broadcast

    def _handle_message(message):
        service = message.application_headers.get('service')
        if service == UPDATE_SERVICE:
            handle_update(message.body)
        elif service == event.SERVICE:
            event.handle_queue_message(message.body)
        elif service == broadcast.REPORT_SERVICE:
            broadcast.handle_abuse_message(message.body)
        elif service == MINUTE:
            log.debug("Minutely housekeeping...")
            from adhocracy.lib import democracy
            democracy.check_adoptions()
        elif service == HOURLY:
            log.debug("Hourly housekeeping...")
            pass
        elif service == DAILY:
            log.debug("Daily housekeeping...")
            # housekeeping
            from adhocracy.lib import watchlist
            watchlist.clean_stale_watches()
            update_solr_for_all_instances()
        model.meta.Session.remove()
    consume(_handle_message)
