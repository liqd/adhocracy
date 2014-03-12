from adhocracy import config
from adhocracy import model
from adhocracy.lib.helpers import site_helper as _site


def is_configured():
    configured = config.get_bool('adhocracy.use_feedback_instance')
    if not configured:
        return False
    if not config.get_bool('adhocracy.feedback_check_instance'):
        return True
    return get_feedback_instance() is not None


def get_feedback_instance():
    return model.Instance.find(config.get('adhocracy.feedback_instance_key'))


def get_categories():
    if not config.get_bool('adhocracy.feedback_use_categories'):
        return []
    feedback_instance = get_feedback_instance()
    return model.CategoryBadge.all(feedback_instance, include_global=False)


def get_proposal_url():
    return _site.base_url(u'/proposal',
                          config.get('adhocracy.feedback_instance_key'))
