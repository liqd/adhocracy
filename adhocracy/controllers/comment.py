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
    
    def _comment_anchor(self, comment):
        
        # for canonical comment discussion, return to the discussion page, 
        # not the main topic page! 
        parent = comment
        while parent.reply:
            parent = parent.reply
        if parent.canonical and parent != comment: 
            return "/comment/%s#c%s" % (str(parent.id), comment.id)
        
        if isinstance(comment.topic, model.Issue):
            return "/issue/%s#c%s" % (str(comment.topic.id), comment.id)
        elif isinstance(comment.topic, model.Motion):
            return "/motion/%s#c%s" % (str(comment.topic.id), comment.id)
        else:
            abort(500, _("Unsupported topic type."))
    
    @RequireInstance
    @RequireInternalRequest(methods=['POST'])
    @ActionProtector(has_permission("comment.create"))
    @validate(schema=CommentCreateForm(), form="create", post_only=True)
    def create(self):
        if request.method == "POST":
            topic = self.form_result.get('topic')
            auth.require_delegateable_perm(topic, 'comment.create')
            canonical = True if self.form_result.get('canonical', 0) == 1 else False
            if canonical:
                if not isinstance(topic, model.Motion):
                    canonical = 0
                else:
                    auth.require_motion_perm(topic, 'comment.create')          
                           
            comment = model.Comment(topic, c.user)
            _text = text.cleanup(self.form_result.get('text'))
            comment.latest = model.Revision(comment, c.user, _text)
            comment.canonical = canonical
           
            if self.form_result.get('reply'):
                comment.reply = self.form_result.get('reply')
            
            model.meta.Session.add(comment)
            model.meta.Session.commit()
            model.meta.Session.refresh(comment)
            
            event.emit(event.T_COMMENT_CREATE, {'comment': comment, 'delegateable': topic},
                       c.user, scopes=[c.instance], topics=[topic, comment])
            
            redirect_to(self._comment_anchor(comment))
        return render('/comment/create.html')
    
    @RequireInstance
    @RequireInternalRequest(methods=['POST'])
    @ActionProtector(has_permission("comment.edit"))
    @validate(schema=CommentEditForm(), form="edit", post_only=True)
    def edit(self, id):
        c.comment = model.Comment.find(id)
        if not c.comment:
            abort(404, _("No comment with ID %s exists") % id)
        auth.require_comment_perm(c.comment, 'comment.delete')
        if request.method == "POST":
            _text = text.cleanup(self.form_result.get('text'))
            c.comment.latest = model.Revision(c.comment, c.user, _text)
            model.meta.Session.add(c.comment.latest)
            model.meta.Session.commit()
            
            event.emit(event.T_COMMENT_EDIT, {'comment': c.comment, 
                                              'delegateable': c.comment.topic},
                       c.user, scopes=[c.instance], topics=[c.comment.topic, c.comment])
            
            redirect_to(self._comment_anchor(c.comment))
        return render('/comment/edit.html')
    
    @ActionProtector(has_permission("comment.view"))
    def redirect(self, id):
        c.comment = model.Comment.find(id, instance_filter=False)
        if not c.comment:
            abort(404, _("No comment with ID %s exists") % id)
        redirect_to(h.instance_url(c.comment.topic.instance, 
                                   path=self._comment_anchor(c.comment)))
    
    @RequireInstance
    @ActionProtector(has_permission("comment.view"))
    def view(self, id):
        c.comment = model.Comment.find(id)
        if not c.comment:
            abort(404, _("No comment with ID %s exists") % id)
        
        return render('/comment/view.html')
    
    @RequireInstance
    @RequireInternalRequest()
    @ActionProtector(has_permission("comment.delete"))
    def delete(self, id):
        c.comment = model.Comment.find(id)
        if not c.comment:
            abort(404, _("No comment with ID %s exists") % id)
        auth.require_comment_perm(c.comment, 'comment.delete')
        c.comment.delete_time = datetime.now()
        model.meta.Session.add(c.comment)
        model.meta.Session.commit()
        
        event.emit(event.T_COMMENT_DELETE, {'comment': c.comment, 
                                            'delegateable': c.comment.topic},
                   c.user, scopes=[c.instance], topics=[c.comment.topic, c.comment])
        
        redirect_to(self._comment_anchor(c.comment))
    
    @RequireInstance
    @ActionProtector(has_permission("comment.view"))    
    def history(self, id):
        c.comment = model.Comment.find(id)
        if not c.comment:
            abort(404, _("No comment with ID %s exists") % id)
        
        
        c.revisions_pager = NamedPager('revisions', c.comment.revisions, tiles.revision.row, count=10, #list_item,
                                     sorts={_("oldest"): sorting.entity_oldest,
                                            _("newest"): sorting.entity_newest},
                                     default_sort=sorting.entity_newest)
        return render('/comment/history.html')
    
    @RequireInstance
    @RequireInternalRequest()
    @ActionProtector(has_permission("comment.edit"))
    @validate(schema=CommentRevertForm(), form="history", post_only=False, on_get=True)
    def revert(self, id):
        c.comment = model.Comment.find(id)
        if not c.comment:
            abort(404, _("No comment with ID %s exists") % id)
        auth.require_comment_perm(c.comment, 'comment.delete')
        revision = self.form_result.get('to')
        if revision.comment != c.comment:
            abort(500, _("You're trying to revert to a revision which is not part of this comments history"))
        c.comment.latest = model.Revision(c.comment, c.user, revision.text)
        model.meta.Session.add(c.comment.latest)
        model.meta.Session.commit()
        
        
        event.emit(event.T_COMMENT_EDIT, {'comment': c.comment, 
                                          'delegateable': c.comment.topic},
                   c.user, scopes=[c.instance], topics=[c.comment.topic, c.comment])
            
        redirect_to(self._comment_anchor(c.comment))
