from pylons import config, tmpl_context as c
from pylons.i18n import _

import scores 

def limit(permission_name):
    cfg = config.get("adhocracy.karma.%s" % permission_name)
    if cfg:
        return int(cfg)
    return 0

def has(user, permission_name):
    if scores.user_score(user) >= limit(permission_name):
        return True
    return False

def message(permission_name):
    messages = {'category.create': _("create a category"),
                'category.edit': _("edit this category"),
                'category.delete': _("delete this category"),
                'comment.create': _("reply in a comment"),
                'comment.edit': _("edit this comment"),
                'comment.delete': _("delete this comment"),
                'karma.give': _("rate this comment"),
                'proposal.create': _("create a proposal"),
                'proposal.edit': _("edit this proposal"),
                'proposal.beginpoll': _("call for a vote"),
                'proposal.endpoll': _("cancel a vote"), 
                'proposal.delete': _("delete a proposal"),
                'issue.create': _("create an issue"),
                'issue.edit': _("edit this issue"),
                'issue.delete': _("delete this issue")}
    return _("You need %s karma to %s") % (limit(permission_name),
                                           messages.get(permission_name, _("do this")))