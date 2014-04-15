from paste.deploy.converters import asbool
from pylons import config

from adhocracy import model
from adhocracy.lib import cache
from adhocracy.lib.helpers import proposal_helper as proposal
from adhocracy.lib.helpers import page_helper as page
from adhocracy.lib.helpers import text_helper as text
from adhocracy.lib.helpers import url as _url


@cache.memoize('comment_url')
def url(comment, member=None, format=None, comment_page=False,
        in_overlay=True, **kwargs):
    if member is None and format is None and not comment_page:
        if isinstance(comment.topic, model.Page):
            if comment.topic.function == model.Page.DESCRIPTION:
                return (proposal.url(comment.topic.proposal,
                                     anchor=u'c%i' % comment.id, **kwargs))
            if comment.topic.is_sectionpage():
                if u'anchor' not in kwargs:
                    kwargs[u'anchor'] = u'c%i' % comment.id
                if in_overlay:
                    kwargs[u'format'] = u'overlay'
                    query = {
                        u'overlay_path': page.url(comment.topic,
                                                  member=u'comments',
                                                  **kwargs),
                        u'overlay_type': u'#overlay-url',
                    }
                    return page.url(comment.topic.sectionpage_root(),
                                    query=query)
                else:
                    return page.url(comment.topic, member=u'comments',
                                    **kwargs),
            return (text.url(comment.topic.variant_head(comment.variant),
                             anchor=u'c%i' % comment.id, **kwargs))
        elif isinstance(comment.topic, model.Proposal):
            return (proposal.url(comment.topic, anchor=u'c%i' % comment.id,
                                 **kwargs))
    return _url.build(comment.topic.instance, 'comment',
                      comment.id, member=member, format=format, **kwargs)


def wording(config=config):
    return asbool(config.get('adhocracy.comment_wording', False))
