"""Setup the adhocracy application"""
import logging

from adhocracy.config.environment import load_environment
from adhocracy import model
from adhocracy.lib import install, search
from adhocracy.model import meta
from pylons import config

log = logging.getLogger(__name__)

def setup_app(command, conf, vars):
    """Place any commands to setup adhocracy here"""
    load_environment(conf.global_conf, conf.local_conf)
    
    if config.get('adhocracy.setup.drop', "OH_NOES") == "KILL_EM_ALL":
        log.warn("DELETING DATABASE AND SEARCH/EVENT INDEX")
        meta.metadata.drop_all(bind=meta.engine)
        import shutil
        shutil.rmtree(search.index_dir())
        search.setup_search()

    # Create the tables if they don't already exist
    meta.metadata.create_all(bind=meta.engine)

    install.setup_entities()