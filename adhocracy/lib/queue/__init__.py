import logging
from amqp import has_queue, post_message, consume

log = logging.getLogger(__name__)

MINUTE = 'minute'
HOURLY = 'hourly'
DAILY = 'daily'
  
def minute(): post_message(MINUTE, '')

def hourly(): post_message(HOURLY, '')

def daily(): post_message(DAILY, '')

# TODO: Inversion of control
def dispatch():
    from adhocracy.model import hooks
    from adhocracy.lib import event
    from adhocracy.lib import broadcast
    def _handle_message(message):
        service = message.application_headers.get('service')
        if service == hooks.SERVICE:
            hooks.handle_queue_message(message.body)
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
            from adhocracy.lib.search import index
            index.optimize()
    consume(_handle_message)