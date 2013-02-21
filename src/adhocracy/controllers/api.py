import logging

from formencode import Schema, validators

from pylons import response
from pylons.decorators import validate

from adhocracy import model
from adhocracy.lib import search as libsearch
from adhocracy.lib.base import BaseController
from adhocracy.lib.templating import render_json


log = logging.getLogger(__name__)


class ProposalFilterForm(Schema):
    allow_extra_fields = True
    proposals_q = validators.String(max=255, not_empty=False, if_empty=None,
                                    if_missing=None)
    callback = validators.String(max=255, not_empty=False, if_empty=None,
                                 if_missing=None)
    proposals_state = validators.String(max=255, not_empty=False,
                                        if_empty=None, if_missing=None)


class ApiController(BaseController):

    @validate(schema=ProposalFilterForm(), post_only=False, on_get=True)
    def proposals(self, format='json'):
        callback = self.form_result.get('callback')

        proposals = libsearch.query.run(None, entity_type=model.Proposal)

        if callback:
            d = render_json(proposals)
            response.content_type = 'application/javascript'
            return "%s(%s)" % (callback, d)
        else:
            return render_json(proposals)
