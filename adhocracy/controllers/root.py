from pylons.i18n import _

from adhocracy.lib.base import *

log = logging.getLogger(__name__)

class RootController(BaseController):

    def index(self, format='html'):
        if c.instance: 
            redirect_to('/issue')
        
        c.instances = model.Instance.all()[:5]           
        c.page = StaticPage('index')
        return render('index.html')
    
    #@RequireInstance
    def dispatch_delegateable(self, id):
        dgb = get_entity_or_abort(model.Delegateable, id, instance_filter=False)
        id = str(id)
        
        if isinstance(dgb, model.Issue):
            redirect_to(h.instance_url(dgb.instance, path="/issue/%s" % id))
        
        redirect_to(h.instance_url(dgb.instance, path="/proposal/%s" % id))
        
    def sitemap_xml(self):
        c.delegateables = []
        def add_delegateables(instance):
            children = model.Delegateable.all(instance=instance)
            c.delegateables.extend(children)
            
        response.content_type = "text/xml"
        
        if c.instance:
            add_delegateables(c.instance)
        else:
            instances = model.Instance.all()
            for instance in instances:
                add_delegateables(instance)
                
        return render("sitemap.xml")
    
    def process(self):
        import adhocracy.lib.queue as queue
        queue.process_messages()
        event.queue_process()
        watchlist.clean_stale_watches()
        democracy.check_adoptions()
        return "everything processed. come back soon ;-)"
            