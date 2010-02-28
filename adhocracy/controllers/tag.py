import logging
from datetime import datetime

from pylons.i18n import _

from adhocracy.lib.base import *
import adhocracy.model.refs as refs
import adhocracy.model.forms as forms

log = logging.getLogger(__name__)

class TagCreateForm(formencode.Schema):
    allow_extra_fields = True
    text = forms.ValidRef()

class TagDeleteForm(formencode.Schema):
    allow_extra_fields = True
    watch = forms.ValidWatch()

class TagController(BaseController):
    
    @RequireInstance
    def index(self, format='html'):
        pass
        
    
    @RequireInstance
    def show(self, id, format='html'):
        pass
      
    
    @RequireInstance 
    def complete(self):
        pass