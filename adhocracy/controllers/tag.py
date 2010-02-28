import logging
from datetime import datetime

from pylons.i18n import _

from adhocracy.lib.base import *
import adhocracy.model.refs as refs
import adhocracy.model.forms as forms

log = logging.getLogger(__name__)


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