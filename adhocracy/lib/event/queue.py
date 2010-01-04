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
    channel.exchange_declare(queue_name(), 'direct', auto_delete=False,
                             durable=True)
    return channel
    
def post_event(event):
    global post_channel
    if not post_channel:
        post_channel = create_channel(write=True)
    
    message = amqp.Message(str(event.id), content_type='application/x-event-id')
    post_channel.basic_publish(message, exchange=queue_name(), 
                               immediate=0)
    
def read_events(callback=None):
    channel = create_channel(read=True)
    qname, _, _ = channel.queue_declare()
    channel.queue_bind(qname, queue_name())
    
    def handle_message(message):
        begin_time = time()
        e = Event.find(int(message.body))
        callback(e)
        log.warn("Queue message - > %sms" % ((time() - begin_time)*1000))
        message.channel.basic_ack(message.delivery_tag)
        
    channel.basic_consume(qname, callback=handle_message)
        
    while channel.callbacks:
        channel.wait()

    channel.close()
    
