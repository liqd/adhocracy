from pylons.i18n import _

from adhocracy.lib.base import *

log = logging.getLogger(__name__)

class RootController(BaseController):

    def index(self, format='html'):
        if c.instance: 
            redirect_to('/instance/%s' % str(c.instance.key))
        
        if format == 'rss':
            query = None
            if c.user:
                query = event.q._or(event.q.scope(c.user), "scope:wall", 
                                    *map(event.q.topic, c.user.instances))
            else:
                query = event.q._or(map(event.q.topic, model.Instance.all()))
            events = event.q.run(query)
            return event.rss_feed(events, _('My Adhocracies'),
                                  h.instance_url(None), 
                                  _("Updates from the Adhocracies in which you are a member"))
        else:
            c.instances = model.Instance.all()[:5]           
            
        return render('index.html')
    
    #@RequireInstance
    def dispatch_delegateable(self, id):
        if c.instance:
            dgb = model.Delegateable.find(id)
        else:
            dgb = model.Delegateable.find(id, instance_filter=False)
        if not dgb:
            abort(404, _("No motion or category with ID %(id)s exists") % {'id': id})
        
        id = str(id)
        
        if isinstance(dgb, model.Category):
            redirect_to(h.instance_url(dgb.instance, path="/category/%s" % id))
        
        if isinstance(dgb, model.Issue):
            redirect_to(h.instance_url(dgb.instance, path="/issue/%s" % id))
        
        redirect_to(h.instance_url(dgb.instance, path="/motion/%s" % id))
        
    def sitemap_xml(self):
        c.delegateables = []
        def add_delegateables(instance):
            children = instance.root.search_children(recurse=True)
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
        event.queue_process()
            