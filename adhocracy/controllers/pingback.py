import cgi
from datetime import datetime

from pylons.controllers import XMLRPCController
from pylons.i18n import _

from adhocracy.lib.base import *

log = logging.getLogger(__name__)

class PingbackController(XMLRPCController):
    
    def pingback_ping(self, sourceURI, targetURI):
        
        return "cheers"
