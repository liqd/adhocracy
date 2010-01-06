from time import time, sleep
import logging

from pylons import config
import amqplib.client_0_8 as amqp

from adhocracy.model import Event

log = logging.getLogger(__name__)
post_channel = None

def has_queue():
    return queue_name() != None

def queue_name():
    return config.get('adhocracy.amqp.event_queue')

def exchange_name():
    return config.get('adhocracy.amqp.event_exchange')

def create_connection():
    host = config.get('adhocracy.amqp.host')
    #userid = config.get('adhocracy.amqp.userid', '')
    #password = config.get('adhocracy.amqp.password', '')
    return amqp.Connection(host=host) #, userid=userid,
                           #password=password)
                           
def create_channel(read=False, write=False):
    conn = create_connection()
    channel = conn.channel()
    channel.access_request('/data', active=True, write=write, read=read)
    channel.exchange_declare(exchange_name(), 'direct', auto_delete=False)
    _, _, _ = channel.queue_declare(queue=queue_name(), durable=False,
                                    exclusive=False, auto_delete=False)
    channel.queue_bind(queue=queue_name(), exchange=exchange_name(),
                       routing_key='event')
    return channel
    
def post_event(event):
    global post_channel
    if not post_channel:
        post_channel = create_channel(write=True)
    
    message = amqp.Message(str(event.id), content_type='application/x-event-id',
                           delivery_mode=2)
    post_channel.basic_publish(message, exchange=exchange_name(),
                               routing_key='event')
    
def read_events(callback):
    channel = create_channel(read=True)
    
    while True:
        begin_time = time()
        message = channel.basic_get(queue_name())
        if not message:
            break
        e = Event.find(int(message.body), instance_filter=False)
        try:
            callback(e)
            channel.basic_ack(message.delivery_tag)
        except Exception, ex:
            log.exception("Processing error: %s" % ex)
        log.warn("Queue message - > %sms" % ((time() - begin_time)*1000))

    channel.close()
        
