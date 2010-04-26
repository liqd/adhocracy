
from common import *

class SearchQueryForm(formencode.Schema):
    allow_extra_fields = True
    serp_q = validators.String(max=255, min=1, if_empty="", if_missing="", not_empty=False)
