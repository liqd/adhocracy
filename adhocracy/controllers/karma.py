import logging
import simplejson 
from datetime import datetime

from pylons.i18n import _
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from adhocracy.lib.base import *
from adhocracy.lib.karma import *
import adhocracy.model.forms as forms

log = logging.getLogger(__name__)

class KarmaGiveForm(formencode.Schema):
    allow_extra_fields = True
    comment = forms.ValidComment(not_empty=True)
    value = validators.Int(min=-1, max=1, not_empty=True)

class KarmaController(BaseController):

    @RequireInstance
    @ActionProtector(has_permission("karma.give"))
    @validate(schema=KarmaGiveForm(), post_only=False, on_get=True)
    def give(self, format="html"):
        if not hasattr(self, 'form_result'):
            abort(400, _("No valid karma data provided"))
        
        comment = self.form_result.get('comment')
        value = self.form_result.get('value')
        if not value in [1, -1]:
            h.flash(_("Invalid karma value. Karma is either positive or negative!"))
            redirect_to("/comment/r/%s" % comment.id)
        
        q = model.meta.Session.query(model.Karma)
        q = q.filter(model.Karma.comment==comment)
        q = q.filter(model.Karma.donor==c.user)
        karma = None
        try:
            karma = q.one()
            if value == -1:
                value = max(-1, karma.value - 1)
            else:
                value = min(1, karma.value + 1)
            karma.value = value
            karma.create_time = datetime.utcnow()
        except NoResultFound:
            karma = model.Karma(value, c.user, comment.creator, comment)
            model.meta.Session.add(karma)
        except MultipleResultsFound:
            log.exception("multiple karmas")
        model.meta.Session.commit()
        
        if format == 'json':
            return simplejson.dumps({'score': comment_score(comment),
                                     'position': position(comment, c.user)})
            
        redirect_to("/comment/r/%s" % comment.id)
