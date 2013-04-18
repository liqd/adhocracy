from cgi import FieldStorage
import logging

import formencode
from formencode import htmlfill, Invalid, validators, All

from pylons import request, tmpl_context as c
from pylons.controllers.util import redirect
from pylons.decorators import validate
from pylons.i18n import _

from adhocracy import config
from adhocracy import forms, model
from adhocracy.forms.common import ValidImageFileUpload
from adhocracy.forms.common import ValidFileUpload
from adhocracy.lib import democracy
from adhocracy.lib import event, helpers as h, sorting, tiles
from adhocracy.lib.auth import can, csrf, require, guard
from adhocracy.lib.base import BaseController
from adhocracy.lib.instance import RequireInstance
from adhocracy.lib.pager import NamedPager
from adhocracy.lib.templating import (render, render_def, render_json,
                                      ret_abort, ret_success)
from adhocracy.lib.util import get_entity_or_abort, validate_ret_url

log = logging.getLogger(__name__)


class CommentNewForm(formencode.Schema):
    allow_extra_fields = True
    topic = forms.ValidDelegateable()
    reply = forms.ValidComment(if_empty=None, if_missing=None)
    wiki = validators.StringBool(not_empty=False, if_empty=False,
                                 if_missing=False)
    variant = forms.VariantName(not_empty=False, if_empty=model.Text.HEAD,
                                if_missing=model.Text.HEAD)
    image = All(ValidImageFileUpload(not_empty=False, if_missing=None),
                ValidFileUpload(not_empty=False),)


class CommentCreateForm(CommentNewForm):
    text = validators.String(max=21000, min=4, not_empty=True)
    sentiment = validators.Int(min=model.Comment.SENT_CON,
                               max=model.Comment.SENT_PRO, if_empty=0,
                               if_missing=0)


class CommentUpdateForm(formencode.Schema):
    allow_extra_fields = True
    text = validators.String(max=21000, min=4, not_empty=True)
    sentiment = validators.Int(min=model.Comment.SENT_CON,
                               max=model.Comment.SENT_PRO, if_empty=0,
                               if_missing=0)


class CommentRevertForm(formencode.Schema):
    allow_extra_fields = True
    to = forms.ValidRevision()


class CommentPurgeForm(formencode.Schema):
    allow_extra_fields = True
    rev = forms.ValidRevision()


class CommentController(BaseController):

    def __init__(self):
        super(CommentController, self).__init__()
        c.api = h.adhocracy_service.RESTAPI()
        c.allow_mediafiles = config.get_bool(
            'adhocracy.delegateable_mediafiles')

    @RequireInstance
    @guard.comment.index()
    def index(self, format='html'):
        comments = model.Comment.all()
        c.comments_pager = NamedPager(
            'comments', comments, tiles.comment.row, count=10,
            sorts={_("oldest"): sorting.entity_oldest,
                   _("newest"): sorting.entity_newest},
            default_sort=sorting.entity_newest)

        if format == 'json':
            return render_json(c.comments_pager)
        else:
            return self.not_implemented(format=format)

    @RequireInstance
    @validate(schema=CommentNewForm(), form="bad_request",
              post_only=False, on_get=True)
    def new(self, errors=None, format='html'):
        c.topic = self.form_result.get('topic')
        c.reply = self.form_result.get('reply')
        c.wiki = self.form_result.get('wiki')
        c.variant = self.form_result.get('variant')
        defaults = dict(request.params)
        if c.reply:
            require.comment.reply(c.reply)
        else:
            require.comment.create_on(c.topic)

        if format == 'ajax':
            html = self._render_ajax_create_form(c.reply, c.topic, c.variant)
        else:
            html = render('/comment/new.html', overlay=format == u'overlay')
        return htmlfill.render(html, defaults=defaults,
                               errors=errors, force_defaults=False)

    @RequireInstance
    @csrf.RequireInternalRequest(methods=['POST'])
    @guard.comment.create()
    def create(self, format='html'):
        try:
            self.form_result = CommentCreateForm().to_python(request.params)
        except Invalid, i:
            return self.new(errors=i.unpack_errors(), format=format)

        topic = self.form_result.get('topic')
        if not topic.allow_comment:
            return ret_abort(
                _("Topic %s does not allow comments") % topic.title,
                code=400, format=format)

        reply = self.form_result.get('reply')
        if reply:
            require.comment.reply(reply)
        else:
            require.comment.create_on(topic)

        variant = self.form_result.get('variant')
        if hasattr(topic, 'variants') and not variant in topic.variants:
            return ret_abort(_("Comment topic has no variant %s") % variant,
                             code=400)

        comment = model.Comment.create(
            self.form_result.get('text'),
            c.user, topic,
            reply=reply,
            wiki=self.form_result.get('wiki'),
            variant=variant,
            sentiment=self.form_result.get('sentiment'),
            with_vote=can.user.vote())

        image = self.form_result.get('image')
        if isinstance(image, FieldStorage):
            response = c.api.add_image(image.filename, image.file.read())
            name = response.json()["name"]
            mediafile = model.MediaFile.create(name)
            mediafile.assignComment(comment, c.user)

        # watch comments by default!
        model.Watch.create(c.user, comment)
        model.meta.Session.commit()
        event.emit(event.T_COMMENT_CREATE, c.user, instance=c.instance,
                   topics=[topic], comment=comment, topic=topic,
                   rev=comment.latest)
        if len(request.params.get('ret_url', '')):
            redirect(request.params.get('ret_url') + "#c" + str(comment.id))
        if format != 'html':
            return ret_success(entity=comment, format=format)
        else:
            return ret_success(entity=comment, format='fwd')

    @RequireInstance
    def edit(self, id, format='html'):
        c.comment = get_entity_or_abort(model.Comment, id)
        require.comment.edit(c.comment)

        image = c.comment.mediafiles[0].name if c.comment.mediafiles else u""
        c.image_src = (u"%s/%s" % (c.api.images_get.url, image)
                       if image else u"")
        extra_vars = {
            'comment': c.comment,
            'allow_mediafiles': c.allow_mediafiles,
            'image_src': c.image_src,
        }

        ret_url = request.params.get(u'ret_url', u'')
        if validate_ret_url(ret_url):
            extra_vars[u'ret_url'] = ret_url
            c.ret_url = ret_url
        if format == 'ajax':
            return render_def('/comment/tiles.html', 'edit_form',
                              extra_vars=extra_vars)
        elif format == 'overlay':
            return render('/comment/edit.html', overlay=True)
        else:
            return render('/comment/edit.html')

    @RequireInstance
    @csrf.RequireInternalRequest(methods=['POST'])
    @validate(schema=CommentUpdateForm(), form="edit", post_only=True)
    def update(self, id, format='html'):
        c.comment = get_entity_or_abort(model.Comment, id)
        require.comment.edit(c.comment)
        rev = c.comment.create_revision(
            self.form_result.get('text'),
            c.user,
            sentiment=self.form_result.get('sentiment'))
        model.meta.Session.commit()
        if can.user.vote():
            decision = democracy.Decision(c.user, c.comment.poll)
            if not decision.result == model.Vote.YES:
                decision.make(model.Vote.YES)
        if 'delete_image' in self.form_result:
            del(c.comment.mediafiles[0])
        image = self.form_result.get('image')
        if isinstance(image, FieldStorage):
            # delete old image (assume there is only one)
            if c.comment.mediafiles:
                del(c.comment.mediafiles[0])
            #add new image
            response = c.api.add_image(image.filename, image.file.read())
            name = response.json()["name"]
            mediafile = model.MediaFile.create(name)
            mediafile.assignComment(c.comment, c.user)
        model.meta.Session.commit()

        # do not modify watch state as comments are always watched

        event.emit(event.T_COMMENT_EDIT, c.user, instance=c.instance,
                   topics=[c.comment.topic], comment=c.comment,
                   topic=c.comment.topic, rev=rev)
        if len(request.params.get('ret_url', '')):
            redirect(request.params.get('ret_url') + "#c" + str(c.comment.id))
        if format != 'html':
            return ret_success(entity=c.comment, format=format)
        else:
            return ret_success(entity=c.comment, format='fwd')

    @RequireInstance
    def show(self, id, format='html'):
        c.comment = get_entity_or_abort(model.Comment, id)
        require.comment.show(c.comment)
        if format == 'fwd':
            redirect(h.entity_url(c.comment))
        elif format == 'json':
            return render_json(c.comment)
        return render('/comment/show.html', overlay=format == u'overlay')

    @RequireInstance
    def ask_delete(self, id, format=u'html'):
        c.comment = get_entity_or_abort(model.Comment, id)
        require.comment.delete(c.comment)
        return render('/comment/ask_delete.html',
                      overlay=format == u'overlay')

    @RequireInstance
    @csrf.RequireInternalRequest()
    def delete(self, id, format='html'):
        c.comment = get_entity_or_abort(model.Comment, id)
        require.comment.delete(c.comment)
        c.comment.delete()
        model.meta.Session.commit()

        event.emit(event.T_COMMENT_DELETE, c.user, instance=c.instance,
                   topics=[c.comment.topic], comment=c.comment,
                   topic=c.comment.topic)
        return ret_success(message=_("The comment has been deleted."),
                           entity=c.comment.topic,
                           format=format)

    @RequireInstance
    def history(self, id, format='html'):
        c.comment = get_entity_or_abort(model.Comment, id)
        require.comment.show(c.comment)
        c.revisions_pager = NamedPager(
            'revisions', c.comment.revisions, tiles.revision.row, count=10,
            sorts={_("oldest"): sorting.entity_oldest,
                   _("newest"): sorting.entity_newest},
            default_sort=sorting.entity_newest)

        if format == 'json':
            return render_json(c.revisions_pager)
        elif format == 'ajax':
            return c.revisions_pager.render_pager()
        elif format == 'overlay':
            return render('/comment/history.html', overlay=True)
        else:
            return render('/comment/history.html')

    @RequireInstance
    @csrf.RequireInternalRequest()
    @guard.perm("comment.edit")
    @validate(schema=CommentRevertForm(), form="history",
              post_only=False, on_get=True)
    def revert(self, id, format='html'):
        c.comment = get_entity_or_abort(model.Comment, id)
        require.comment.revert(c.comment)
        revision = self.form_result.get('to')
        if revision.comment != c.comment:
            return ret_abort(_("You're trying to revert to a revision which "
                               "is not part of this comment's history"),
                             code=400, format=format)
        rev = c.comment.create_revision(revision.text,
                                        c.user,
                                        sentiment=revision.sentiment)
        model.meta.Session.commit()
        event.emit(event.T_COMMENT_EDIT, c.user, instance=c.instance,
                   topics=[c.comment.topic], comment=c.comment,
                   topic=c.comment.topic, rev=rev)
        return ret_success(message=_("The comment has been reverted."),
                           entity=c.comment, format=format)

    @RequireInstance
    @csrf.RequireInternalRequest()
    @guard.perm("global.admin")
    @validate(schema=CommentPurgeForm(), form="history",
              post_only=False, on_get=True)
    def purge_history(self, id, format='html'):
        c.comment = get_entity_or_abort(model.Comment, id)

        require.comment.revert(c.comment)
        revision = self.form_result.get('rev')
        if revision.comment != c.comment:
            return ret_abort(_("You're trying to purge a revision which "
                               "is not part of this comment's history"),
                             code=400, format=format)

        model.meta.Session.delete(revision)
        model.meta.Session.commit()
        return ret_success(message=_("The comment revision has been deleted."),
                           entity=c.comment, format=format)

    def create_form(self, topic):
        topic = model.Delegateable.find(int(topic))
        if topic is None:
            return ret_abort(_('Wrong topic'))  # FIXME: better msg
        require.comment.create_on(topic)
        variant = request.params.get('variant', None)
        if hasattr(topic, 'variants') and not variant in topic.variants:
            return ret_abort(_("Comment topic has no variant %s") % variant,
                             code=400)
        return self._render_ajax_create_form(None, topic, variant)

    def _render_ajax_create_form(self, parent, topic, variant, ret_url=None):
        '''
        render a create form fragment that can be inserted loaded
        into another page.
        '''
        if ret_url is None:
            ret_url = ''

        # FIXME: uncomment the format parameter when we have javascript
        # code to submit the form with ajax and replace the form with the
        # response
        # For now, it renders the form with error messages or redirects
        # the user to the new comments anchor on success
        template_args = dict(parent=parent,
                             topic=topic,
                             variant=variant,
                             allow_mediafiles=c.allow_mediafiles,
                             #format="ajax",
                             ret_url=ret_url,
                             )
        return render_def('/comment/tiles.html', 'create_form',
                          template_args)

    def reply_form(self, id):
        parent = get_entity_or_abort(model.Comment, int(id))
        require.comment.reply(parent)
        topic = parent.topic
        variant = getattr(topic, 'variant', None)
        ret_url = request.params['ret_url']
        return self._render_ajax_create_form(parent, topic, variant, ret_url)
