"""Setup the adhocracy application"""
import logging
import os
import shutil
import os.path

from adhocracy.config.environment import load_environment
from adhocracy import model
from adhocracy.lib import install, search, openidstore, util, init_site
from adhocracy.lib.queue import init_queue
from adhocracy.model import meta
from pylons import config

log = logging.getLogger(__name__)

def setup_app(command, conf, vars):
    """Place any commands to setup adhocracy here"""
    load_environment(conf.global_conf, conf.local_conf)
    init_site()
    # disable delayed execution
    config['adhocracy.amqp.host'] = None 
    init_queue()
    
    if config.get('adhocracy.setup.drop', "OH_NOES") == "KILL_EM_ALL":
        log.warn("DELETING DATABASE AND SEARCH/EVENT INDEX")
        meta.metadata.drop_all(bind=meta.engine)
        index_path = util.get_site_path(*search.SITE_INDEX_DIR)
        if os.path.exists(index_path):
            shutil.rmtree(index_path)
    
    # Create the tables if they don't already exist
    meta.metadata.create_all(bind=meta.engine)
    try:
        store = openidstore._create_sql_store()
        store.createTables()
    except Exception, e:
        log.warn("Creating OpenID SQL tables failed. No reason to panic: %s" % e)
    
    if not config.get('skip_setupentities'):
        install.setup_entities()
        
    search.init_search()