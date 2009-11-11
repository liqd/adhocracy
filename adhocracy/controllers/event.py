import lucene

from pylons.i18n import _

from adhocracy.lib.base import *
import adhocracy.lib.helpers as h
from adhocracy.model.forms import EditorAddForm, EditorRemoveForm

log = logging.getLogger(__name__)

class EventController(BaseController):
    
    @ActionProtector(has_permission("global.admin"))  
    def all(self):
        events = event.q.run("+type:event")
        c.event_pager = NamedPager('events', events, tiles.event.list_item, count=50)
        return render('/event/all.html')