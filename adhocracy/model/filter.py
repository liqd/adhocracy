from beaker.util import ThreadLocal

thread_instance = ThreadLocal()

def setup_thread(instance):
    global thread_instance
    thread_instance.put(instance)
    
def has_instance():
    return thread_instance.get() != None

def get_instance():
    return thread_instance.get()


