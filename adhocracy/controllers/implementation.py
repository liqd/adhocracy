import cgi
from datetime import datetime

from pylons.i18n import _
from formencode import foreach, Invalid

from adhocracy.lib.base import *
import adhocracy.lib.text as text
import adhocracy.forms as forms


log = logging.getLogger(__name__)


class ImplementationController(BaseController):
    
    @RequireInstance
    def index(self, proposal_id, format="html"):
        c.proposal = get_entity_or_abort(model.Proposal, proposal_id)     
        require.proposal.show(c.proposal)
        c.proposal_tile = tiles.proposal.ProposalTile(c.proposal)
        
        return render("/implementation/index.html")
    
    
    @RequireInstance
    def new(self, proposal_id, errors=None):
        c.proposal = get_entity_or_abort(model.Proposal, proposal_id)     
        require.proposal.show(c.proposal)
        c.proposal_tile = tiles.proposal.ProposalTile(c.proposal)
        
        return render("/implementation/new.html")
    
    
    @RequireInstance
    @RequireInternalRequest(methods=['POST'])
    def create(self, proposal_id, format='html'):
        c.proposal = get_entity_or_abort(model.Proposal, proposal_id)     
        require.proposal.show(c.proposal)
        
        # TODO implement
    

    def edit(self, proposal_id, id, errors={}):
        return self.not_implemented()
    
    
    def update(self, proposal_id, id, format='html'):
        return self.not_implemented()
    
    
    @RequireInstance
    def show(self, proposal_id, id, format='html'):
        c.proposal = get_entity_or_abort(model.Proposal, proposal_id)     
        require.proposal.show(c.proposal)
        c.proposal_tile = tiles.proposal.ProposalTile(c.proposal)
        
        return render("/implementation/show.html")
    
    
    @RequireInstance
    def ask_delete(self, proposal_id, id):
        c.proposal = get_entity_or_abort(model.Proposal, proposal_id)     
        require.proposal.show(c.proposal)
        c.proposal_tile = tiles.proposal.ProposalTile(c.proposal)
        
        return render("/implementation/ask_delete.html")
    
    
    @RequireInstance
    @RequireInternalRequest()
    def delete(self, proposal_id, id):
        c.proposal = get_entity_or_abort(model.Proposal, proposal_id)     
        require.proposal.show(c.proposal)
        
        # TODO implement
        
        redirect(h.entity_url(c.proposal))
    