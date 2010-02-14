from datetime import datetime

from pylons.i18n import _

from adhocracy.lib.base import *
import adhocracy.lib.text as text
import adhocracy.model.forms as forms
import adhocracy.lib.democracy as democracy

log = logging.getLogger(__name__)

class CommentNewForm(formencode.Schema):
    allow_extra_fields = True
    topic = forms.ValidDelegateable()
    reply = forms.ValidComment(if_empty=None)

class CommentCreateForm(CommentNewForm):
    text = validators.String(max=20000, min=4, not_empty=True)
    canonical = validators.StringBool(not_empty=True)
    
class CommentUpdateForm(formencode.Schema):
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
        topic = self.form_result.get('topic')
        if canonical and not isinstance(topic, model.Proposal):
            abort(400, _("Trying to create a provision on an issue"))
        elif canonical and not topic.is_mutable():
            abort(403, h.immutable_proposal_message())
        comment = model.Comment.create(self.form_result.get('text'), 
                                       c.user, topic, 
                                       reply=self.form_result.get('reply'), 
                                       canonical=canonical)
        model.meta.Session.commit()
        if h.has_permission('vote.cast'):
            decision = democracy.Decision(c.user, comment.poll)
            decision.make(model.Vote.YES)
        watchlist.check_watch(comment)
        event.emit(event.T_COMMENT_CREATE, c.user, instance=c.instance, 
                   topics=[topic], comment=comment, topic=topic)
        redirect_to(h.entity_url(comment))
    
    @RequireInstance
    @ActionProtector(has_permission("comment.edit"))
    def edit(self, id):
        c.comment = self._get_mutable_or_abort(id)
        return render('/comment/edit.html')
    
    @RequireInstance
    @RequireInternalRequest(methods=['POST'])
    @ActionProtector(has_permission("comment.edit"))
    @validate(schema=CommentUpdateForm(), form="edit", post_only=True)
    def update(self, id):
        c.comment = self._get_mutable_or_abort(id)
        c.comment.create_revision(self.form_result.get('text'), c.user)
        model.meta.Session.commit()
        #if h.has_permission('vote.cast'):
        #    decision = democracy.Decision(c.user, c.comment.poll)
        #    if not decision.is_decided():
        #        decision.make(model.Vote.YES)
        watchlist.check_watch(c.comment)
        event.emit(event.T_COMMENT_EDIT, c.user, instance=c.instance, 
                   topics=[c.comment.topic], comment=c.comment, 
                   topic=c.comment.topic)
        redirect_to(h.entity_url(c.comment))
    
    @RequireInstance
    @ActionProtector(has_permission("comment.view"))
    def show(self, id, format='html'):
        c.comment = get_entity_or_abort(model.Comment, id)
        if format == 'fwd':
            redirect_to(h.entity_url(c.comment))
        elif format == 'json':
            return render_json(c.comment)
        return render('/comment/show.html')
    
    
    @RequireInstance
    @ActionProtector(has_permission("comment.delete"))
    def ask_delete(self, id):
        c.comment = self._get_mutable_or_abort(id)
        return render('/comment/ask_delete.html')
    
    
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
        if c.comment.root().canonical:
            redirect_to(h.entity_url(c.comment.topic, member='canonicals'))
        redirect_to(h.entity_url(c.comment.topic))
    
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
        redirect_to(h.entity_url(c.comment))
    
    # get a comment for editing, checking that it is mutable. 
    def _get_mutable_or_abort(self, id):
        comment = get_entity_or_abort(model.Comment, id)
        if not comment.is_mutable():
            abort(403, h.immutable_proposal_message())
        return comment
