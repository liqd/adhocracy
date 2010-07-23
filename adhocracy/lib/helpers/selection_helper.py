
from adhocracy.lib import cache

import proposal_helper as proposal
import url as _url

@cache.memoize('selection_url')
def url(selection, **kwargs):
    url = proposal.url(selection.proposal, member='implementation')
    url += "/" + str(selection.id)
    return _url.append_member_and_format(url, **kwargs)