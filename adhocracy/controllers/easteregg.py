from datetime import datetime
import logging

from pylons import request, response, tmpl_context as c
from pylons.controllers.util import redirect
from pylons.decorators import validate

from adhocracy import model
from adhocracy.lib import helpers as h
from adhocracy.lib.auth import require
from adhocracy.lib.base import BaseController
from adhocracy.lib.static import StaticPage
from adhocracy.lib.templating import render
from adhocracy.lib.util import get_entity_or_abort

from proposal import ProposalFilterForm


log = logging.getLogger(__name__)


class EastereggController(BaseController):

    def get_easteregg(self):
        response.content_type = "text/plain"
        return render("easteregg.json")

