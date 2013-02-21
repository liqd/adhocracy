import logging
from time import time

import amqplib.client_0_8 as amqp
from pylons import config

log = logging.getLogger(__name__)
post_channel = None


def has_queue():
    return config.get('adhocracy.amqp.host') is not None


def queue_name():
    return config.get('adhocracy.amqp.queue',
                      'adhocracy.queue')


def exchange_name():
    return config.get('adhocracy.amqp.exchange',
                      'adhocracy.exchange')


def create_connection():
    host = config.get('adhocracy.amqp.host')
    port = config.get('adhocracy.amqp.port', '5672')
    return amqp.Connection(host="%s:%s" % (host, port))


def create_channel(read=False, write=False):
    conn = create_connection()
    channel = conn.channel()
    channel.access_request('/data', active=True, write=write, read=read)
    channel.exchange_declare(exchange_name(), 'direct',
                             durable=True,
                             auto_delete=False)
    _, _, _ = channel.queue_declare(queue=queue_name(),
                                    durable=True,
                                    exclusive=False,
                                    auto_delete=False)
    channel.queue_bind(queue=queue_name(),
                       exchange=exchange_name(),
                       routing_key='adhocracy')
    return channel


def post_message(service, text):
    global post_channel
    try:
        if post_channel is None:
            post_channel = create_channel(write=True)

        message = amqp.Message(text,
                               content_type='adhocracy/%s' % service,
                               application_headers={'service': service},
                               delivery_mode=2)
        post_channel.basic_publish(message,
                                   exchange=exchange_name(),
                                   routing_key='adhocracy')
    except Exception:
        log.exception("Error posting to queue")


def callback_wrapper(channel, callback):
    def _handle(message):
        begin_time = time()
        log.debug("%r, body: %r" % (message.application_headers, message.body))
        try:
            callback(message)
        except Exception, ex:
            log.exception(ex)
        channel.basic_ack(message.delivery_tag)
        log.debug("Queue message %s - > %.2fms" % (
            message.application_headers,
            (time() - begin_time) * 1000))
    return _handle


def consume(callback):
    channel = create_channel(read=True)
    callback = callback_wrapper(channel, callback)
    channel.basic_consume(queue_name(), callback=callback)
    while channel.callbacks:
        channel.wait()
    channel.close()
