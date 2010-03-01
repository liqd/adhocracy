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
    def index(self, format='html'):
        tags = model.Tag.popular_tags(limit=200)
        c.tags = sorted(text.tag_cloud_normalize(tags), key=lambda (k, v): k.name)
        return render("/tag/index.html")
        
    
    @RequireInstance
    def show(self, id, format='html'):
        return render("/tag/show.html")
      
    
    @RequireInstance 
    def complete(self):
        pass