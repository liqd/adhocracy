from datetime import datetime

from pylons.i18n import _

from adhocracy.lib.base import *
import adhocracy.lib.text as text
import adhocracy.model.forms as forms

log = logging.getLogger(__name__)

class CommentCreateForm(formencode.Schema):
    allow_extra_fields = True
    text = validators.String(max=20000, min=4, not_empty=True)
    canonical = validators.Int(if_empty=0, if_missing=0, not_empty=False)
    topic = forms.ValidDelegateable()
    reply = forms.ValidComment(if_empty=None)
    
class CommentEditForm(formencode.Schema):
    allow_extra_fields = True
    text = validators.String(max=20000, min=4, not_empty=True)

class CommentRevertForm(formencode.Schema):
    allow_extra_fields = True
    to = forms.ValidRevision()

class CommentController(BaseController):
    
    @RequireInstance
    @RequireInternalRequest(methods=['POST'])
    @ActionProtector(has_permission("comment.create"))
    @validate(schema=CommentCreateForm(), form="create", post_only=True)
    def create(self):
        if request.method == "POST":
            topic = self.form_result.get('topic')
            canonical = True if self.form_result.get('canonical', 0) == 1 else False
            if canonical and not isinstance(topic, model.Proposal):
                canonical = False
            elif canonical and not democracy.is_proposal_mutable(topic):
                abort(403, h.immutable_proposal_message())
            
            comment = model.Comment(topic, c.user)
            _text = text.cleanup(self.form_result.get('text'))
            comment.latest = model.Revision(comment, c.user, _text)
            comment.canonical = canonical
           
            if self.form_result.get('reply'):
                comment.reply = self.form_result.get('reply')
            
            karma = model.Karma(1, c.user, c.user, comment)
            
            model.meta.Session.add(comment)
            model.meta.Session.add(karma)
            model.meta.Session.commit()
            model.meta.Session.refresh(comment)
            
            watchlist.check_watch(comment)
            
            event.emit(event.T_COMMENT_CREATE, c.user, instance=c.instance, 
                       topics=[topic], comment=comment, topic=topic)
            
            self.redirect(comment.id)
        else:
            try: 
                c.topic = forms.ValidDelegateable(not_empty=True).to_python(request.params.get('topic'))
                c.reply = forms.ValidComment(not_empty=True).to_python(request.params.get('reply'))
                return render('/comment/create.html')
            except formencode.Invalid, i:
                abort(400, i)
    
    @RequireInstance
    @RequireInternalRequest(methods=['POST'])
    @ActionProtector(has_permission("comment.edit"))
    @validate(schema=CommentEditForm(), form="edit", post_only=True)
    def edit(self, id):
        c.comment = get_entity_or_abort(model.Comment, id)
        if c.comment.canonical and not democracy.is_proposal_mutable(c.comment.topic):
            abort(403, h.immutable_proposal_message())
        if request.method == "POST":
            _text = text.cleanup(self.form_result.get('text'))
            c.comment.latest = model.Revision(c.comment, c.user, _text)
            model.meta.Session.add(c.comment.latest)
            model.meta.Session.commit()
            
            watchlist.check_watch(c.comment)
            
            event.emit(event.T_COMMENT_EDIT, c.user, instance=c.instance, 
                       topics=[c.comment.topic], comment=c.comment, 
                       topic=c.comment.topic)
            
            self.redirect(c.comment.id)
        return render('/comment/edit.html')
    
    @ActionProtector(has_permission("comment.view"))
    def redirect(self, id):
        c.comment = get_entity_or_abort(model.Comment, id, instance_filter=False)
        
        with_path = lambda path: redirect_to(h.instance_url(c.comment.topic.instance, 
                                                            path=path))
        # for canonical comment discussion, return to the discussion page, 
        # not the main topic page! 
        parent = c.comment
        while parent.reply:
            parent = parent.reply
        
        # TODO make canonical subcomments visible via javascript instead, don't 
        # go to comment single view. 
        if parent.canonical and parent != c.comment: 
            with_path("/comment/%s#c%s" % (str(parent.id), c.comment.id))
        if isinstance(c.comment.topic, model.Issue):
            with_path("/issue/%s#c%s" % (str(c.comment.topic.id), c.comment.id))
        elif isinstance(c.comment.topic, model.Proposal):
            with_path("/proposal/%s#c%s" % (str(c.comment.topic.id), c.comment.id))
        else:
            abort(500, _("Unsupported topic type."))
    
    @RequireInstance
    @ActionProtector(has_permission("comment.view"))
    def view(self, id):
        c.comment = get_entity_or_abort(model.Comment, id)
        return render('/comment/view.html')
    
    @RequireInstance
    @RequireInternalRequest()
    @ActionProtector(has_permission("comment.delete"))
    def delete(self, id):
        c.comment = get_entity_or_abort(model.Comment, id)
        if c.comment.canonical and not democracy.is_proposal_mutable(c.comment.topic):
            abort(403, h.immutable_proposal_message())
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
        c.comment = get_entity_or_abort(model.Comment, id)
        if c.comment.canonical and not democracy.is_proposal_mutable(c.comment.topic):
            abort(403, h.immutable_proposal_message())
        revision = self.form_result.get('to')
        if revision.comment != c.comment:
            abort(400, _("You're trying to revert to a revision which is not part of this comments history"))
        c.comment.latest = model.Revision(c.comment, c.user, revision.text)
        model.meta.Session.add(c.comment.latest)
        model.meta.Session.commit()
        
        event.emit(event.T_COMMENT_EDIT, c.user, instance=c.instance, 
                   topics=[c.comment.topic], comment=c.comment, 
                   topic=c.comment.topic)
            
        self.redirect(c.comment.id)
