"""Setup the adhocracy application"""
import logging
import os, os.path
import shutil
import os.path

from adhocracy.config.environment import load_environment
from adhocracy import model
from adhocracy.lib import install, search, openidstore, util, init_site
from adhocracy.lib.queue import init_queue
from adhocracy.model import meta
from pylons import config

import migrate.versioning.api as migrateapi
from migrate.versioning.exceptions import DatabaseAlreadyControlledError
from sqlalchemy.exc import NoSuchTableError

log = logging.getLogger(__name__)

def setup_app(command, conf, vars):
    """Place any commands to setup adhocracy here"""
    load_environment(conf.global_conf, conf.local_conf)
    init_site()
    # disable delayed execution
    config['adhocracy.amqp.host'] = None    
    init_queue()
    
    index_path = util.get_site_path(*search.SITE_INDEX_DIR)
    if os.path.exists(index_path):
        shutil.rmtree(index_path)
    
    if config.get('adhocracy.setup.drop', "OH_NOES") == "KILL_EM_ALL":
        log.warn("DELETING DATABASE AND SEARCH/EVENT INDEX")
        meta.data.drop_all(bind=meta.engine)
        #migrateapi.downgrade(url, migrate_repo, version=0)
    
    # Create the tables if they don't already exist
    url = config.get('sqlalchemy.url') 
    migrate_repo = os.path.join(os.path.dirname(__file__), 'migration')
    repo_version = migrateapi.version(migrate_repo)
    
    try:
        db_version = migrateapi.db_version(url, migrate_repo)
        if db_version < repo_version:
            migrateapi.upgrade(url, migrate_repo)
    except NoSuchTableError:
        meta.data.create_all(bind=meta.engine)
        migrateapi.version_control(url, migrate_repo, version=repo_version)
    
    if not config.get('skip_setupentities'):
        install.setup_entities()
        
    search.init_search()
    



