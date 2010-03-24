import logging
from datetime import datetime

from pylons.i18n import _

from adhocracy.lib.base import *
import adhocracy.lib.text as text
import adhocracy.model.refs as refs
import adhocracy.model.forms as forms

log = logging.getLogger(__name__)


class TagProposalFilterForm(formencode.Schema):
    allow_extra_fields = True
    proposals_state = validators.String(max=255, not_empty=False, if_empty=None, if_missing=None)


class TagController(BaseController):
    
    @RequireInstance
    @ActionProtector(has_permission("tag.view"))
    def index(self, format='html'):
        tags = model.Tag.popular_tags(limit=200)
        c.tags = sorted(text.tag_cloud_normalize(tags), key=lambda (k, c, v): k.name.lower())
        return render("/tag/index.html")
        
    
    @RequireInstance
    @ActionProtector(has_permission("tag.view"))
    @validate(schema=TagProposalFilterForm(), post_only=False, on_get=True)
    def show(self, id, format='html'):
        c.tag = get_entity_or_abort(model.Tag, id)
        proposals = libsearch.query.run(c.tag.name, instance=c.instance,  
                                        fields=['tags'], entity_type=model.Proposal)
        
        if format == 'json':
            return render_json(proposals)
            
        if self.form_result.get('proposals_state'): 
            proposals = model.Proposal.filter_by_state(self.form_result.get('proposals_state'), 
                                                       proposals)
        
        # TODO "Similar tags"
        c.proposals_pager = pager.proposals(proposals)
        tags = model.Tag.similar_tags(c.tag, limit=50)
        c.cloud_tags = sorted(text.tag_cloud_normalize(tags), key=lambda (k, c, v): k.name)
        
        return render("/tag/show.html")
      
    
    @RequireInstance
    @ActionProtector(has_permission("tag.view"))    
    def autocomplete(self):
        prefix = unicode(request.params.get('q', ''))
        (base, prefix) = text.tag_split_last(prefix)
        results = []
        for (tag, freq) in model.Tag.complete(prefix, 10):
            display = "%s (%s)" % (tag.name, freq) 
            full = base + tag.name + ", "
            results.append(dict(display=display, tag=full))
        return render_json(results)