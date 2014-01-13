#!/usr/bin/env python
"""
Replay all events in order to create Notification entries to the database which
do not exist yet.
"""

# boilerplate code. copy that
import os
import sys
from argparse import ArgumentParser
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
# /end boilerplate code

from paste.deploy import appconfig
import pylons
from pylons.i18n.translation import _get_translator

from adhocracy.config.environment import load_environment
from adhocracy.lib.event.notification import notify
from adhocracy.model import meta, Event


def load_config(filename):
    conf = appconfig('config:' + os.path.abspath(filename) + '#content')
    load_environment(conf.global_conf, conf.local_conf)
    translator = _get_translator(pylons.config.get('lang'))
    pylons.translator._push_object(translator)


def parse_args():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("conf_file", help="configuration to use")
    return parser.parse_args()


def main():
    args = parse_args()
    load_config(args.conf_file)
    all_events = meta.Session.query(Event).all()

    for event in all_events:
        notify(event, database_only=True)

    meta.Session.commit()

if __name__ == '__main__':
    sys.exit(main())
