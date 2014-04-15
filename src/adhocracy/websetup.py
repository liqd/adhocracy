"""Setup the adhocracy application"""
import logging

import alembic
import alembic.config
import pylons
import pylons.test

from adhocracy.config.environment import load_environment
from adhocracy.lib import install
from adhocracy.model import meta

log = logging.getLogger(__name__)


def setup_app(command, conf, vars):
    """Place any commands to setup adhocracy here"""

    config_filename = conf.filename
    if not pylons.test.pylonsapp:
        conf = load_environment(conf.global_conf, conf.local_conf,
                                with_db=False)
    conf['config_filename'] = config_filename
    _setup(conf)


def _setup(config):
    # disable delayed execution
    # FIXME: still do this with rq instead of rabbitmq
    # NOTE: this is called from tests so it may have side effects

    if config.get('adhocracy.setup.drop', "OH_NOES") == "KILL_EM_ALL":
        meta.data.drop_all(bind=meta.engine)
        meta.engine.execute("DROP TABLE IF EXISTS alembic_version")

    alembic_cfg = alembic.config.Config(config['config_filename'])

    if meta.engine.has_table('alembic_version'):
        alembic.command.upgrade(alembic_cfg, 'head')
        initial_setup = False
    else:
        # Create the tables
        meta.data.create_all(bind=meta.engine)
        alembic.command.stamp(alembic_cfg, 'head')
        initial_setup = True

    install.setup_entities(config, initial_setup)
