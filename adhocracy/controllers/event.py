from pylons.i18n import _

from adhocracy.lib.base import *
import adhocracy.lib.helpers as h
from adhocracy.model.forms import EditorAddForm, EditorRemoveForm

log = logging.getLogger(__name__)

class EventController(BaseController):
    
    @ActionProtector(has_permission("global.admin"))  
    def all(self):
        query = model.meta.Session.query(model.Event)
        query = query.order_by(model.Event.time.desc())
        query = query.limit(200)
        c.event_pager = NamedPager('events', query.all(), tiles.event.list_item, count=50)
        return render('/event/all.html')