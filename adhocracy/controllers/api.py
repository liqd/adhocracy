from datetime import datetime
from pylons.i18n import _
import formencode

from adhocracy.lib.base import *

log = logging.getLogger(__name__)

class ProposalFilterForm(formencode.Schema):
    allow_extra_fields = True
    proposals_q = validators.String(max=255, not_empty=False, if_empty=None, if_missing=None)
    callback = validators.String(max=255, not_empty=False, if_empty=None, if_missing=None)
    proposals_state = validators.String(max=255, not_empty=False, if_empty=None, if_missing=None)

class ApiController(BaseController):

    @validate(schema=ProposalFilterForm(), post_only=False, on_get=True)
    def proposals(self, format='json'):
        query = self.form_result.get('proposals_q')
        callback = self.form_result.get('callback')

        proposals = libsearch.query.run(None, entity_type=model.Proposal)

    	if callback: 
		d = render_json(proposals)
		response.content_type = 'application/javascript'
		return "%s(%s)" %(callback, d)
    	else:
		return render_json(proposals)
    
