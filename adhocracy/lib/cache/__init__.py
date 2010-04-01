import logging

import adhocracy.model.hooks as hooks
import adhocracy.model as model

from util import memoize
from invalidate import *


log = logging.getLogger(__name__)

def setup_cache():
    log.info("Setting up memcache-related persistence hooks...")
    hooks.patch_default(model.User, invalidate_user)
    hooks.patch_default(model.Vote, invalidate_vote)
    hooks.patch_default(model.Page, invalidate_page)
    hooks.patch_default(model.Proposal, invalidate_delegateable)
    hooks.patch_default(model.Issue, invalidate_delegateable)
    hooks.patch_default(model.Delegation, invalidate_delegation)
    hooks.patch_default(model.Revision, invalidate_revision)
    hooks.patch_default(model.Comment, invalidate_comment)
    hooks.patch_default(model.Poll, invalidate_poll)
    hooks.patch_default(model.Tagging, invalidate_tagging)
    hooks.patch_default(model.Text, invalidate_text)