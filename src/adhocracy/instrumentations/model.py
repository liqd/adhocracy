import importlib

from pyprol.measurement import measurement
from logging import getLogger

log = getLogger(u'adhocracy.instrumentations.model')

def inject(config):
    try:
        _adhocracy_model = importlib.import_module("adhocracy.model")
        _before_commit = _adhocracy_model.before_commit

        def before_commit(session):
            measure = measurement.enable(u"adhocracy.model.before_commit")
            result = _before_commit(session)
            measurement.disable(measure)
            return result

        _adhocracy_model.before_commit = before_commit
        log.info("injected into adhocracy.model.before_commit")

    except ImportError as e:
        log.info("Could not import `adhocracy.model`")
        log.debug(e)

