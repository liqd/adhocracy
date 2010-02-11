
from amqp import has_queue, post_message, read_messages
from registry import init_hooks, register, process_messages
from registry import INSERT, UPDATE, DELETE

def init_queue():
    init_hooks()