
from amqp import has_queue, post_message, consume

HOUSEKEEP = 'ping'
  
def ping():
    post_message(HOUSEKEEP, 'ping')

# TODO: Inversion of control
def dispatch():
    from adhocracy.model import hooks
    from adhocracy.lib import event
    def _handle_message(message):
        service = message.application_headers.get('service')
        if service == hooks.SERVICE:
            hooks.handle_queue_message(message.body)
        elif service == event.SERVICE:
            event.handle_queue_message(message.body)
        elif service == HOUSEKEEP:
            # housekeeping
            from adhocracy.lib import watchlist
            watchlist.clean_stale_watches()
            from adhocracy.lib import democracy
            democracy.check_adoptions()
    consume(_handle_message)