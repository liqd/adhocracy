import logging

import pylons
from pylons import tmpl_context as c
from pylons import request
from pylons.util import ContextObj, PylonsContext

from adhocracy.model import instance_filter
from adhocracy.controllers import comment as Comment

from adhocracy.lib.emailcomments import permissions, util
from adhocracy.lib.search import index

from webob import Request

log = logging.getLogger(__name__)


def setup_req():
    '''create request'''
    request = Request.blank("http://localhost")
    pylons.request._push_object(request)


def setup_c(user_obj):
    '''
    setup the tmpl_context:
    sunburnt_connection: solr
    user, instance: repoze / permissions
    '''
    c = ContextObj()
    py_obj = PylonsContext()
    py_obj.tmpl_context = c
    pylons.tmpl_context._push_object(c)
    c = pylons.tmpl_context

    c.instance = instance_filter.get_instance()
    c.user = user_obj
    c.sunburnt_connection = index.make_connection()


def comment(user_obj, comment_obj, text, sentiment):
    '''
    If comment does not already exist (inbox sync):
    Setup of template-ontext, request and permissions for instance/user.
    Finally teardown instance, request-environment and template-context.
    '''
    if util.comment_exists(text, user_obj, comment_obj.id):
        return
    instance_filter.setup_thread(comment_obj.topic.instance)
    setup_req()
    setup_c(user_obj)
    permissions.setup_perm(request.environ, c.user)
    try:
        Comment._create(user=c.user,
                        reply=comment_obj,
                        topic=comment_obj.topic,
                        text=text,
                        wiki=0,
                        variant=comment_obj.variant,
                        instance=c.instance,
                        sentiment=sentiment)
    except Exception as e:
        log.info("error in creating comment: {0}".format(e))
        util.error_mail_to_user(401, user_obj, comment_obj)
    finally:
        instance_filter.teardown_thread()
        request.environ = {}
        del c.user
        del c.instance
        del c.sunburnt_connection
