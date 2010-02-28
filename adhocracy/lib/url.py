import urllib
import adhocracy.model as model
from pylons import tmpl_context as c, request


class UrlConstructionException(Exception): 
    pass


def instance_url(instance, path=None):
    url = "http://"
    if instance is not None:
        url += instance.key + "."
    url += request.environ.get('adhocracy.domain')
    if path is not None:
        url += path
    return str(url)

    
def _append_member_and_format(url, member=None, format=None):
    if member is not None:
        url += '/' + member
    if format is not None:
        url += '.' + format.lower()
    return str(url)


def _common_url_builder(instance, base, id, **kwargs):
    url = instance_url(instance, path='/' + base + '/' + str(id))
    return _append_member_and_format(url, **kwargs)


def user_url(user, instance=None, **kwargs):
    if instance is None:
        instance = c.instance
    return _common_url_builder(instance, 'user', user.user_name, **kwargs)

    
def proposal_url(proposal, **kwargs):
    return _common_url_builder(proposal.instance, 'proposal', 
                               proposal.id, **kwargs)

    
def issue_url(issue, **kwargs):
    return _common_url_builder(issue.instance, 'issue', 
                               issue.id, **kwargs)


def delegateable_url(delegateable, **kwargs):
    return _common_url_builder(delegateable.instance, 'd', 
                               delegateable.id)

    
def poll_url(poll, **kwargs):
    return _common_url_builder(poll.scope.instance, 'poll', 
                               poll.id, **kwargs)


def tag_url(tag, instance=None, **kwargs):
    if instance is None:
        instance = c.instance
    return _common_url_builder(instance, 'tag',
                               urllib.quote(tag.name), **kwargs)


def comment_url(comment, member=None, format=None, comment_page=False, **kwargs):
    if member is None and format is None and not comment_page:
        if isinstance(comment.topic, model.Issue):
            return issue_url(comment.topic) + '#c' + str(comment.id)
        elif isinstance(comment.topic, model.Proposal):
            if comment.root().canonical:
                return proposal_url(comment.topic, member='canonicals') \
                        + '#c' + str(comment.id)
            return proposal_url(comment.topic) + '#c' + str(comment.id)
    return _common_url_builder(comment.topic.instance, 'comment', 
                               comment.id, member=member, format=format, **kwargs)

    
def instance_entity_url(instance, member=None, format=None, **kwargs):
    if member is None and format is None:
        return instance_url(instance, path='/issue')
    return _common_url_builder(instance, 'instance', 
                               instance.key, member=member, format=format, **kwargs)

    
def delegation_url(delegation, **kwargs):
    return _common_url_builder(delegation.scope.instance, 'delegation', 
                               delegation.id, **kwargs)


def entity_url(entity, **kwargs):
    if isinstance(entity, model.User):
        return user_url(entity, **kwargs)
    elif isinstance(entity, model.Proposal):
        return proposal_url(entity, **kwargs)
    elif isinstance(entity, model.Issue):
        return issue_url(entity, **kwargs)
    elif isinstance(entity, model.Delegateable):
        return delegateable_url(entity, **kwargs)
    elif isinstance(entity, model.Poll):
        return poll_url(entity, **kwargs)
    elif isinstance(entity, model.Comment):
        return comment_url(entity, **kwargs)
    elif isinstance(entity, model.Instance):
        return instance_entity_url(entity, **kwargs)
    elif isinstance(entity, model.Delegation):
        return delegation_url(entity, **kwargs)
    elif isinstance(entity, model.Tag):
        return tag_url(entity, **kwargs)
    raise UrlConstructionException()

