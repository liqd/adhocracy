import logging
from datetime import datetime

from pylons.i18n import _

from adhocracy.lib.base import *
import adhocracy.lib.text as text
import adhocracy.model.refs as refs
import adhocracy.model.forms as forms

log = logging.getLogger(__name__)


class TagController(BaseController):
    
    @RequireInstance
    @ActionProtector(has_permission("tag.view"))
    def index(self, format='html'):
        tags = model.Tag.popular_tags(limit=200)
        c.tags = sorted(text.tag_cloud_normalize(tags), key=lambda (k, c, v): k.name)
        return render("/tag/index.html")
        
    
    @RequireInstance
    @ActionProtector(has_permission("tag.view"))
    def show(self, id, format='html'):
        c.tag = get_entity_or_abort(model.Tag, id)
        proposals = libsearch.query.run(c.tag.name, instance=c.instance,  
                                        fields=['tags'], entity_type=model.Proposal)
        
        if format == 'json':
            return render_json(proposals)
        
        # TODO "Similar tags"
        c.proposals_pager = pager.proposals(proposals)
        return render("/tag/show.html")
      
    
    @RequireInstance 
    def complete(self):
        pass