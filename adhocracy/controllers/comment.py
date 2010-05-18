from datetime import datetime

from pylons.i18n import _

from adhocracy.lib.base import *
import adhocracy.lib.text as text
import adhocracy.forms as forms
import adhocracy.lib.democracy as democracy

log = logging.getLogger(__name__)


class CommentNewForm(formencode.Schema):
    allow_extra_fields = True
    topic = forms.ValidDelegateable()
    reply = forms.ValidComment(if_empty=None, if_missing=None)
    wiki = validators.StringBool(not_empty=False, if_empty=False, if_missing=False)
    canonical = validators.StringBool(not_empty=False, if_empty=False, if_missing=False)
    variant = forms.VariantName(not_empty=False, if_empty=model.Text.HEAD, if_missing=model.Text.HEAD)


class CommentCreateForm(CommentNewForm):
    text = validators.String(max=21000, min=4, not_empty=True)
    sentiment = validators.Int(min=model.Comment.SENT_CON, max=model.Comment.SENT_PRO, if_empty=0, if_missing=0)
    
    
class CommentUpdateForm(formencode.Schema):
    allow_extra_fields = True
    text = validators.String(max=21000, min=4, not_empty=True)
    sentiment = validators.Int(min=model.Comment.SENT_CON, max=model.Comment.SENT_PRO, if_empty=0, if_missing=0)


class CommentRevertForm(formencode.Schema):
    allow_extra_fields = True
    to = forms.ValidRevision()


class CommentController(BaseController):
    
    @RequireInstance
    def index(self, format='html'):
        require.comment.index()
        comments = model.Comment.all()
        c.comments_pager = NamedPager('comments', comments, 
                                       tiles.comment.full, count=10, #list_item,
                                       sorts={_("oldest"): sorting.entity_oldest,
                                              _("newest"): sorting.entity_newest},
                                       default_sort=sorting.entity_newest)
        if format == 'json':
            return render_json(c.comments_pager)
        
        return self.not_implemented(format=format)
    
    
    @RequireInstance
    @validate(schema=CommentCreateForm(), form="bad_request", 
              post_only=False, on_get=True)
    def new(self):
        c.topic = self.form_result.get('topic')
        c.reply = self.form_result.get('reply')
        c.wiki = self.form_result.get('wiki')
        c.canonical = self.form_result.get('canonical')
        c.variant = self.form_result.get('variant')
        if c.reply:
            require.comment.reply(c.reply)
        else: 
            require.comment.create_on(c.topic, canonical=c.canonical)
        return render('/comment/new.html')
    
    
    @RequireInstance
    @RequireInternalRequest(methods=['POST'])
    @validate(schema=CommentCreateForm(), form="new", post_only=True)
    def create(self, format='html'):
        canonical = self.form_result.get('canonical')
        topic = self.form_result.get('topic')
        reply = self.form_result.get('reply')
        
        if canonical and not isinstance(topic, model.Proposal):
            return ret_abort(_("Trying to create a provision on a page"), code=400)
        if reply:
            require.comment.reply(reply)
        else: 
            require.comment.create_on(topic, canonical=canonical)
            
        variant = self.form_result.get('variant')
        if hasattr(topic, 'variants') and not variant in topic.variants:
            return ret_abort(_("Comment topic has no variant %s") % variant, code=400)
        
        comment = model.Comment.create(self.form_result.get('text'), 
                                       c.user, topic, 
                                       reply=reply, 
                                       wiki=self.form_result.get('wiki'),
                                       canonical=canonical,
                                       variant=variant,
                                       sentiment=self.form_result.get('sentiment'), 
                                       with_vote=can.user.vote())
        model.meta.Session.commit()
        watchlist.check_watch(comment)
        event.emit(event.T_COMMENT_CREATE, c.user, instance=c.instance, 
                   topics=[topic], comment=comment, topic=topic, rev=comment.latest)
        return ret_success(entity=comment, format=format if format != 'html' else None)
    
    
    @RequireInstance
    def edit(self, id):
        c.comment = get_entity_or_abort(model.Comment, id)
        require.comment.edit(c.comment)
        return render('/comment/edit.html')
    
    
    @RequireInstance
    @RequireInternalRequest(methods=['POST'])
    @validate(schema=CommentUpdateForm(), form="edit", post_only=True)
    def update(self, id, format='html'):
        c.comment = get_entity_or_abort(model.Comment, id)
        require.comment.edit(c.comment)
        rev = c.comment.create_revision(self.form_result.get('text'), 
                                        c.user,
                                        sentiment=self.form_result.get('sentiment'))
        model.meta.Session.commit()
        if can.user.vote():
            decision = democracy.Decision(c.user, c.comment.poll)
            if not decision.result == model.Vote.YES:
                decision.make(model.Vote.YES)
        model.meta.Session.commit()
        watchlist.check_watch(c.comment)
        event.emit(event.T_COMMENT_EDIT, c.user, instance=c.instance, 
                   topics=[c.comment.topic], comment=c.comment, 
                   topic=c.comment.topic, rev=rev)
        return ret_success(entity=c.comment, format=format if format != 'html' else None)
    
    
    @RequireInstance
    def show(self, id, format='html'):
        c.comment = get_entity_or_abort(model.Comment, id)
        require.comment.show(c.comment)
        if format == 'fwd':
            redirect(h.entity_url(c.comment))
        elif format == 'json':
            return render_json(c.comment)
        return render('/comment/show.html')
    
    
    @RequireInstance
    def ask_delete(self, id):
        c.comment = get_entity_or_abort(model.Comment, id)
        require.comment.delete(c.comment)
        return render('/comment/ask_delete.html')
    
    
    @RequireInstance
    @RequireInternalRequest()
    def delete(self, id, format='html'):
        c.comment = get_entity_or_abort(model.Comment, id)
        require.comment.delete(c.comment)
        c.comment.delete()
        model.meta.Session.commit()
        
        event.emit(event.T_COMMENT_DELETE, c.user, instance=c.instance, 
                   topics=[c.comment.topic], comment=c.comment, 
                   topic=c.comment.topic)
        if c.comment.root().canonical:
            redirect(h.entity_url(c.comment.topic, member='canonicals'))
        return ret_success(message=_("The comment has been deleted."), entity=c.comment.topic, 
                           format=format)
    
    
    @RequireInstance
    def history(self, id, format='html'):
        c.comment = get_entity_or_abort(model.Comment, id)
        require.comment.show(c.comment)
        c.revisions_pager = NamedPager('revisions', c.comment.revisions, 
                                       tiles.revision.row, count=10, #list_item,
                                     sorts={_("oldest"): sorting.entity_oldest,
                                            _("newest"): sorting.entity_newest},
                                     default_sort=sorting.entity_newest)
        if format == 'json':
            return render_json(c.revisions_pager)
        return render('/comment/history.html')
    
    
    @RequireInstance
    @RequireInternalRequest()
    @ActionProtector(has_permission("comment.edit"))
    @validate(schema=CommentRevertForm(), form="history", post_only=False, on_get=True)
    def revert(self, id, format='html'):
        c.comment = get_entity_or_abort(model.Comment, id)
        require.comment.revert(c.comment)
        revision = self.form_result.get('to')
        if revision.comment != c.comment:
            return ret_abort(_("You're trying to revert to a revision which is not part of this comments history"),
                             code=400, format=format)
        rev = c.comment.create_revision(revision.text, c.user, sentiment=revision.sentiment)
        model.meta.Session.commit()
        event.emit(event.T_COMMENT_EDIT, c.user, instance=c.instance, 
                   topics=[c.comment.topic], comment=c.comment, 
                   topic=c.comment.topic, rev=rev)
        return ret_success(message=_("The comment has been reverted."), entity=c.comment, 
                           format=format if format != 'html' else None)
    
