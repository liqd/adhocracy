from time import time, sleep
import logging

from pylons import config
import amqplib.client_0_8 as amqp

log = logging.getLogger(__name__)
post_channels = {}

def has_queue():
    return config.get('adhocracy.amqp.host') \
           is not None

def queue_name(service):
    return config.get('adhocracy.amqp.queue')

def exchange_name(service):
    return config.get('adhocracy.amqp.exchange')

def create_connection():
    host = config.get('adhocracy.amqp.host')
    return amqp.Connection(host=host)
                           
def create_channel(service, read=False, write=False):
    conn = create_connection()
    channel = conn.channel()
    channel.access_request('/data', active=True, write=write, read=read)
    channel.exchange_declare(exchange_name(service), 'direct', auto_delete=False)
    _, _, _ = channel.queue_declare(queue=queue_name(service), 
                                    durable=False,
                                    exclusive=False, 
                                    auto_delete=False)
    channel.queue_bind(queue=queue_name(service), 
                       exchange=exchange_name(service),
                       routing_key=service)
    return channel

    
def post_message(service, text):
    global post_channels
    if service not in post_channels.keys():
        post_channels[service] = create_channel(service, write=True)
    
    message = amqp.Message(text, content_type='application/adhocracy',
                           delivery_mode=2)
    post_channels[service].basic_publish(message, 
                                        exchange=exchange_name(service),
                                        routing_key=service)
    
def read_messages(service, callback):
    channel = create_channel(service, read=True)
    
    while True:
        begin_time = time()
        message = channel.basic_get(queue_name(service))
        if not message:
            break
        try:
            callback(message.body)
            channel.basic_ack(message.delivery_tag)
        except Exception, ex:
            log.exception("Processing error: %s" % ex)
        log.warn("Queue message - > %sms" % ((time() - begin_time)*1000))
    channel.close()
