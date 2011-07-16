from adhocracy import model
from adhocracy.lib import cache
from adhocracy.lib.helpers import proposal_helper as proposal
from adhocracy.lib.helpers import text_helper as text
from adhocracy.lib.helpers import url as _url


@cache.memoize('comment_url')
def url(comment, member=None, format=None, comment_page=False, **kwargs):
    if member is None and format is None and not comment_page:
        if isinstance(comment.topic, model.Page):
            if comment.topic.function == model.Page.DESCRIPTION:
                return (proposal.url(comment.topic.proposal) + '#c' +
                        str(comment.id))
            return (text.url(comment.topic.variant_head(comment.variant)) +
                    '#c' + str(comment.id))
        elif isinstance(comment.topic, model.Proposal):
            return proposal.url(comment.topic) + '#c' + str(comment.id)
    return _url.build(comment.topic.instance, 'comment',
                      comment.id, member=member, format=format, **kwargs)
