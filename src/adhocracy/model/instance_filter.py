from beaker.util import ThreadLocal

thread_instance = ThreadLocal()


def setup_thread(instance):
    global thread_instance
    thread_instance.put(instance)


def teardown_thread():
    '''
    A counterpart for setup_thread(), probly only
    useful in test_code
    '''
    global thread_instance
    try:
        thread_instance.remove()
    except AttributeError:
        # no value saved
        pass


def has_instance():
    return thread_instance.get() != None


def get_instance():
    return thread_instance.get()
