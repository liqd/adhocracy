from datetime import datetime

from pylons.i18n import _

from adhocracy.lib.base import *
import adhocracy.lib.text as text
import adhocracy.model.forms as forms

log = logging.getLogger(__name__)

class CommentNewForm(formencode.Schema):
    allow_extra_fields = True
    topic = forms.ValidDelegateable()
    reply = forms.ValidComment(if_empty=None)

class CommentCreateForm(CommentNewForm):
    text = validators.String(max=20000, min=4, not_empty=True)
    canonical = validators.StringBool(not_empty=True)
    
class CommentEditForm(formencode.Schema):
    allow_extra_fields = True
    text = validators.String(max=20000, min=4, not_empty=True)

class CommentRevertForm(formencode.Schema):
    allow_extra_fields = True
    to = forms.ValidRevision()

class CommentController(BaseController):
    
    @RequireInstance
    @ActionProtector(has_permission("comment.create"))
    @validate(schema=CommentCreateForm(), form="bad_request", 
              post_only=False, on_get=True)
    def new(self):
        c.topic = self.form_result.get('topic')
        c.reply = self.form_result.get('reply')
        return render('/comment/new.html')
    
    @RequireInstance
    @RequireInternalRequest(methods=['POST'])
    @ActionProtector(has_permission("comment.create"))
    @validate(schema=CommentCreateForm(), form="new", post_only=True)
    def create(self):
        canonical = self.form_result.get('canonical')
        print "CCC", canonical, "FOO", request.params.get('canonical')
        topic = self.form_result.get('topic')
        if canonical and not isinstance(topic, model.Proposal):
            abort(400, _("Trying to create a provision on an issue"))
        elif canonical and not democracy.is_proposal_mutable(topic):
            abort(403, h.immutable_proposal_message())
        comment = model.Comment.create(self.form_result.get('text'), 
                                       c.user, topic, 
                                       reply=self.form_result.get('reply'), 
                                       canonical=canonical)
        model.meta.Session.commit()
        watchlist.check_watch(comment)
        event.emit(event.T_COMMENT_CREATE, c.user, instance=c.instance, 
                   topics=[topic], comment=comment, topic=topic)
        self._redirect(comment)
    
    @RequireInstance
    @ActionProtector(has_permission("comment.edit"))
    def edit(self, id):
        c.comment = self._get_mutable_or_abort(id)
        return render('/comment/edit.html')
    
    @RequireInstance
    @RequireInternalRequest(methods=['POST'])
    @ActionProtector(has_permission("comment.edit"))
    @validate(schema=CommentEditForm(), form="edit", post_only=True)
    def update(self, id):
        c.comment = self._get_mutable_or_abort(id)
        c.comment.create_revision(self.form_result.get('text'), c.user)
        model.meta.Session.commit()
        watchlist.check_watch(c.comment)
        event.emit(event.T_COMMENT_EDIT, c.user, instance=c.instance, 
                   topics=[c.comment.topic], comment=c.comment, 
                   topic=c.comment.topic)
        self._redirect(c.comment)
    
    @RequireInstance
    @ActionProtector(has_permission("comment.view"))
    def show(self, id, format='html'):
        c.comment = get_entity_or_abort(model.Comment, id)
        if format == 'fwd':
            self._redirect(c.comment)
        elif format == 'json':
            return render_json(c.comment)
        return render('/comment/show.html')
    
    @RequireInstance
    @RequireInternalRequest()
    @ActionProtector(has_permission("comment.delete"))
    def delete(self, id):
        c.comment = self._get_mutable_or_abort(id)
        c.comment.delete()
        model.meta.Session.commit()
        
        event.emit(event.T_COMMENT_DELETE, c.user, instance=c.instance, 
                   topics=[c.comment.topic], comment=c.comment, 
                   topic=c.comment.topic)
        
        redirect_to("/d/%s" % c.comment.topic.id)
    
    @RequireInstance
    @ActionProtector(has_permission("comment.view"))    
    def history(self, id):
        c.comment = get_entity_or_abort(model.Comment, id)
        c.revisions_pager = NamedPager('revisions', c.comment.revisions, 
                                       tiles.revision.row, count=10, #list_item,
                                     sorts={_("oldest"): sorting.entity_oldest,
                                            _("newest"): sorting.entity_newest},
                                     default_sort=sorting.entity_newest)
        return render('/comment/history.html')
    
    @RequireInstance
    @RequireInternalRequest()
    @ActionProtector(has_permission("comment.edit"))
    @validate(schema=CommentRevertForm(), form="history", post_only=False, on_get=True)
    def revert(self, id):
        c.comment = self._get_mutable_or_abort(id)
        revision = self.form_result.get('to')
        if revision.comment != c.comment:
            abort(400, _("You're trying to revert to a revision which is not part of this comments history"))
        c.comment.create_revision(revision.text, c.user)
        model.meta.Session.commit()
        
        event.emit(event.T_COMMENT_EDIT, c.user, instance=c.instance, 
                   topics=[c.comment.topic], comment=c.comment, 
                   topic=c.comment.topic)
            
        self._redirect(c.comment)
    
    # get a comment for editing, checking that it is mutable. 
    def _get_mutable_or_abort(self, id):
        comment = get_entity_or_abort(model.Comment, id)
        if comment.canonical and not democracy.is_proposal_mutable(comment.topic):
            abort(403, h.immutable_proposal_message())
        return comment
    
    def _redirect(self, comment):
        path = None 
        if isinstance(c.comment.topic, model.Issue):
            path = "/issue/%s#c%s" % (comment.topic.id, comment.id)
        elif isinstance(c.comment.topic, model.Proposal):
            path = "/proposal/%s#c%s" % (comment.topic.id, comment.id)
        else:
            abort(500, _("Unsupported topic type."))
        redirect_to(h.instance_url(comment.topic.instance, path=path))
