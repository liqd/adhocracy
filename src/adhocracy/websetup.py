"""Setup the adhocracy application"""
import logging
import os
import os.path

import pylons
import pylons.test
from pylons import config

import migrate.versioning.api as migrateapi
try:
    from migrate.versioning.exceptions import DatabaseAlreadyControlledError
    from migrate.versioning.exceptions import DatabaseNotControlledError
except ImportError:
    # location changed in 0.6.1
    from migrate.exceptions import DatabaseAlreadyControlledError
    from migrate.exceptions import DatabaseNotControlledError


from adhocracy.config.environment import load_environment
from adhocracy.lib import install
from adhocracy.model import meta

log = logging.getLogger(__name__)


def setup_app(command, conf, vars):
    """Place any commands to setup adhocracy here"""
    if not pylons.test.pylonsapp:
        load_environment(conf.global_conf, conf.local_conf, with_db=False)
    _setup(conf)


def _setup(config):
    # disable delayed execution
    # config['adhocracy.amqp.host'] = None
    # FIXME: still do this with rq instead of rabbitmq
    # NOTE: this is called from tests so it may have side effects

    # Create the tables if they don't already exist
    url = config.get('sqlalchemy.url')
    migrate_repo = os.path.join(os.path.dirname(__file__), 'migration')
    repo_version = migrateapi.version(migrate_repo)

    if config.get('adhocracy.setup.drop', "OH_NOES") == "KILL_EM_ALL":
        meta.data.drop_all(bind=meta.engine)
        meta.engine.execute("DROP TABLE IF EXISTS migrate_version")

    try:
        db_version = migrateapi.db_version(url, migrate_repo)
        if db_version < repo_version:
            migrateapi.upgrade(url, migrate_repo)
        initial_setup = False
    except DatabaseNotControlledError:
        meta.data.create_all(bind=meta.engine)
        migrateapi.version_control(url, migrate_repo, version=repo_version)
        initial_setup = True

    install.setup_entities(initial_setup)
