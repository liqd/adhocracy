"""
Utility code to use in command line scripts.
You need some boilerplate code to import from this module
Cause it's probably not in the python path::

  # boilerplate code. copy that to a new commandline script
  import os
  import sys
  sys.path.insert(0,  os.path.abspath(os.path.dirname(__file__)))
  from common import create_parser, get_instances, load_from_args
  # /end boilerplate code

* Parse command line arguments with a preconfigured argparser::

    parser = create_parser('description of the command...', use_instances=True)
    # You can add more arguments to the parser
    # parser.add_argument(...)
    args = parser.parse_args()
    # args will contain all command line args
    load_from_args(args)
    instances = get_instances(args)  # returns instance objects
"""

try:
    from argparse import ArgumentParser
except ImportError:
    print ('This script uses argparse. It is part of python 2.7/3.2\n'
           'and can be installed from pypi for other versions:\n'
           'http://pypi.python.org/pypi/argparse')
    exit(1)
import os

from sqlalchemy import engine_from_config
from paste.deploy import appconfig

from adhocracy.config.environment import load_environment
from adhocracy.model import Instance

section = 'content'


def config_from_args(args):
    filename = args.file
    section = args.section
    return appconfig('config:%s#%s' % (os.path.abspath(filename), section))


def load_config(config):
    return load_environment(config.global_conf, config.local_conf)


def load_from_args(args):
    config = config_from_args(args)
    return load_config(config)


def create_parser(description, use_instance=True,
                  instance_help='Instances to consider'):
    parser = ArgumentParser(description=description)
    parser.add_argument("file", help="configuration file to use",
                        metavar="<config file>")
    parser.add_argument("-n", default=section, dest="section",
                        help=('name of the "app:"-section to use. (default: '
                              '%s)' % section))
    if use_instance:
        parser.add_argument(
            "-i", "--instance", metavar='INSTANCE', nargs="*",
            dest="instances", help=instance_help, action="append")
    return parser


def get_instances(args):
    '''
    Flatten out the instances parsed by a parser from create_parser
    used with `use_instance=True`
    '''
    if args.instances:
        keys = [item for sublist in args.instances for item in
                sublist]
        instances = []
        for key in keys:
            obj = Instance.find(key)
            if obj is None:
                raise ValueError("Instance '%s' does not exist" % key)
            instances.append(obj)
        return instances
    return None


def get_engine(conf, echo=True):
    return engine_from_config(conf.local_conf, echo=echo)
