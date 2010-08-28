import os
import sys
import logging

import paste.script
from paste.script.command import Command
from paste.script.util.logging_config import fileConfig

class AdhocracyCommand(Command):
    parser = Command.standard_parser(verbose=True)
    parser.add_option('-c', '--config', dest='config',
            default='development.ini', help='Config file to use.')
    default_verbosity = 1
    group_name = 'adhocracy'

    def _load_config(self):
        from paste.deploy import appconfig
        from adhocracy.config.environment import load_environment
        if not self.options.config:
            msg = 'No config file supplied'
            raise self.BadCommand(msg)
        self.filename = os.path.abspath(self.options.config)
        try:
            fileConfig(self.filename)
        except Exception: pass
        conf = appconfig('config:' + self.filename)
        load_environment(conf.global_conf, conf.local_conf)
        

    def _setup_app(self):
        cmd = paste.script.appinstall.SetupCommand('setup-app') 
        cmd.run([self.filename])
        
        
        
class Background(AdhocracyCommand):
    '''Run Adhocracy background jobs.'''
    summary = __doc__.split('\n')[0]
    usage = __doc__
    max_args = None
    min_args = None

    def command(self):
        self._load_config()
        import queue
        queue.dispatch()
        
        

