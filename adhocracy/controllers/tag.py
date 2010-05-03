import logging
from datetime import datetime

from pylons.i18n import _

from adhocracy.lib.base import *
import adhocracy.lib.text as text
import adhocracy.model.refs as refs
import adhocracy.forms as forms

log = logging.getLogger(__name__)


class TagProposalFilterForm(formencode.Schema):
    allow_extra_fields = True
    proposals_state = validators.String(max=255, not_empty=False, if_empty=None, if_missing=None)
    
class TaggingCreateForm(formencode.Schema):
    allow_extra_fields = True
    tags = validators.String(max=10000, not_empty=True)
    delegateable = forms.ValidDelegateable()

class TaggingDeleteForm(formencode.Schema):
    allow_extra_fields = True
    tagging = forms.ValidTagging()


class TagController(BaseController):
    
    @RequireInstance
    def index(self, format='html'):
        require.tag.index()
        tags = model.Tag.popular_tags(limit=200)
        if format == 'json':
            return render_json(tags)
        c.tags = sorted(text.tag_cloud_normalize(tags), 
                        key=lambda (k, c, v): k.name.lower())
        return render("/tag/index.html")
        
    
    @RequireInstance
    @validate(schema=TagProposalFilterForm(), post_only=False, on_get=True)
    def show(self, id, format='html'):
        c.tag = get_entity_or_abort(model.Tag, id)
        require.tag.show(c.tag)
        require.proposal.index()
        proposals = libsearch.query.run(c.tag.name, instance=c.instance,  
                                        fields=['tags'], entity_type=model.Proposal)
        
        if format == 'json':
            return render_json(c.tag)
            
        if self.form_result.get('proposals_state'): 
            proposals = model.Proposal.filter_by_state(self.form_result.get('proposals_state'), 
                                                       proposals)
        
        # TODO "Similar tags"
        c.proposals_pager = pager.proposals(proposals)
        tags = model.Tag.similar_tags(c.tag, limit=50)
        c.cloud_tags = sorted(text.tag_cloud_normalize(tags), key=lambda (k, c, v): k.name)
        return render("/tag/show.html")
    
    
    @RequireInstance
    @validate(schema=TaggingCreateForm(), form="bad_request", post_only=False, on_get=True)
    def create(self, format='html'):
        require.tag.create()
        delegateable = self.form_result.get('delegateable')
        for tag_text in text.tag_split(self.form_result.get('tags')):
            if not model.Tagging.find_by_delegateable_name_creator(delegateable, 
                                                                   tag_text, c.user):
                tagging = model.Tagging.create(delegateable, tag_text, c.user)
        model.meta.Session.commit()
        redirect(h.entity_url(delegateable, format=format))
        
        
    @RequireInstance
    @RequireInternalRequest()
    @validate(schema=TaggingDeleteForm(), form="bad_request", post_only=False, on_get=True)
    def untag(self, format='html'):
        tagging = self.form_result.get('tagging')
        require.tag.delete(tagging)
        tagging.delete()
        model.meta.Session.commit()
        redirect(h.entity_url(tagging.delegateable, format=format))
      
    
    @RequireInstance  
    def autocomplete(self):
        require.tag.index()
        prefix = unicode(request.params.get('q', ''))
        (base, prefix) = text.tag_split_last(prefix)
        results = []
        for (tag, freq) in model.Tag.complete(prefix, 10):
            display = "%s (%s)" % (tag.name, freq) 
            full = base + tag.name + ", "
            results.append(dict(display=display, tag=full))
        return render_json(results)