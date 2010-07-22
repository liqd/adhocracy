import urllib
import adhocracy.model as model
import text
from pylons import tmpl_context as c, request


class UrlConstructionException(Exception): 
    pass


def instance_url(instance, path=None):
    url = "http://"
    if instance is not None:
        url += instance.key + u"."
    url += request.environ.get('adhocracy.domain')
    port = int(request.environ.get('SERVER_PORT'))
    if port != 80:
        url += ':' + str(port)
    if path is not None:
        url += path
    return url

    
def append_member_and_format(url, member=None, format=None):
    if member is not None:
        url += u'/' + member
    if format is not None:
        url += u'.' + format.lower()
    return url


def build(instance, base, id, query=None, **kwargs):
    url = instance_url(instance, path=u'/' + base + u'/' + unicode(id))
    url = append_member_and_format(url, **kwargs)
    if query is not None:
        for k, v in query.items():
            query[unicode(k).encode('ascii', 'ignore')] = unicode(v).encode('utf-8')
        url = url + u'?' + unicode(urllib.urlencode(query))
    return url #.encode('utf-8')


def user_url(user, instance=None, **kwargs):
    if instance is None:
        instance = c.instance
    return build(instance, 'user', user.user_name, **kwargs)

    
def proposal_url(proposal, **kwargs):
    ext = str(proposal.id) + '-' + text.label2alias(proposal.label)
    return build(proposal.instance, 'proposal', 
                               ext, **kwargs)


def delegateable_url(delegateable, **kwargs):
    return build(delegateable.instance, 'd', 
                               delegateable.id)

    
def poll_url(poll, **kwargs):
    return build(poll.scope.instance, 'poll', 
                               poll.id, **kwargs)


def page_url(page, in_context=True, member=None, **kwargs):
    if in_context and page.proposal and not member:
        return proposal_url(page.proposal, **kwargs)
    label = urllib.quote(page.label.encode('utf-8'))
    return build(page.instance, 'page', 
                               label, member=member, **kwargs)


def text_url(text, with_text=True, **kwargs):
    url = page_url(text.page, in_context=text == text.page.variant_head(text.variant))
    if text.page.has_variants and text.variant != model.Text.HEAD:
        url += u'/' + urllib.quote(text.variant.encode('utf-8'))
    if with_text and text != text.page.variant_head(text.variant):
        url += u';' + str(text.id)
    return append_member_and_format(url, **kwargs)


def selection_url(selection, **kwargs):
    url = proposal_url(selection.proposal, member="implementation")
    url += "/" + str(selection.id)
    return append_member_and_format(url, **kwargs)


def tag_url(tag, instance=None, **kwargs):
    if instance is None:
        instance = c.instance
    ident = None
    try:
        ident = urllib.quote(tag.name.encode('utf-8'))
    except KeyError:
        ident = tag.id
    return build(instance, u'tag', ident, **kwargs)


def comment_url(comment, member=None, format=None, comment_page=False, **kwargs):
    if member is None and format is None and not comment_page:
        if isinstance(comment.topic, model.Page):
            if comment.topic.function == model.Page.DESCRIPTION:
                return proposal_url(comment.topic.proposal) + '#c' + str(comment.id)
            return text_url(comment.topic.variant_head(comment.variant)) + '#c' + str(comment.id)
        elif isinstance(comment.topic, model.Proposal):
            return proposal_url(comment.topic) + '#c' + str(comment.id)
    return build(comment.topic.instance, 'comment', 
                               comment.id, member=member, format=format, **kwargs)

    
def instance_entity_url(instance, member=None, format=None, **kwargs):
    #if member is None and format is None:
    #    return instance_url(instance, path='/instance')
    return build(instance, 'instance', 
                               instance.key, member=member, format=format, **kwargs)

    
def delegation_url(delegation, **kwargs):
    return build(delegation.scope.instance, 'delegation', 
                               delegation.id, **kwargs)




