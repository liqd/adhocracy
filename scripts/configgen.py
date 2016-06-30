#!/usr/bin/env python
from __future__ import unicode_literals
import io
import os
import re
import argparse


class config:
    def __init__(self, name="", context="", typ="", description=""):
        self.name = name
        self.context = context
        self.typ = typ
        self.description = description

    def get_package(self):
        return re.match(r""".*?([^ ]*config).*""", self.context).group(1)


class configs:
    def __init__(self):
        self.confs = dict()

    def update(self, conf):
        if conf.name not in self.confs:
            self.confs[conf.name] = list()
        self.confs[conf.name].append(conf)


def find_py_files(dir):
    for dirpath, dirname, filenames in os.walk(dir):
        for filename in filenames:
            if os.path.splitext(filename)[1] in [".py", ".html"]:
                yield os.path.join(dirpath, filename)


def find_config(filename, cfgs=None):
    with io.open(filename, 'r', encoding="UTF-8") as f:
        code = f.read()
    for m in re.finditer(r"""(?x)^.*(config (?:\.get_?(.*?)\(|\[)
            '(?P<name>.*?)'
            (?:,.*?)? (?:\)|\])).*$ # group 1 for complete config
            """, code, re.MULTILINE):
        if cfgs is not None:
            fds = config(m.group('name'), m.group(), m.group(2))
            cfgs.update(fds)
        yield m.group('name')


def find_pylons_import(filename):
    with io.open(filename, 'r', encoding="UTF-8") as f:
        code = f.read()
    if re.search(r"""from pylons import config""", code) is not None:
        return filename


def get_sorted_configs(dir, cfgs=None):
    s = set()
    for f in find_py_files(dir):
        s.update(find_config(f, cfgs))
    return sorted(s)


def get_pylons_imports(dir, cfgs=None):
    s = set()
    for f in find_py_files(dir):
        s.add(find_pylons_import(f))
    return sorted(s)


def get_defaults(filename):
    with io.open(filename, 'r', encoding="UTF-8") as f:
        code = f.read()
    defaults = re.search(r"""DEFAULTS = \{((.*?))\}""", code,
                         re.MULTILINE | re.DOTALL).group(1)
    cfgs = configs()
    for m in re.finditer(r"""^ [^u\n]*?\'(.*?)\'.*?,\n""",
                         defaults, re.MULTILINE):
        fds = config(m.group(1), m.group())
        cfgs.update(fds)
    return cfgs


def print_cfgs(cfgs, cfgs2=configs()):
    for key in sorted(cfgs.confs.keys()):
        if key not in cfgs2.confs.keys():
            print(key),
            print(": "),
            for conf in cfgs.confs[key]:
                print(conf.typ),
                None
            print("")


def print_confs():
    cfgs = configs()
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    get_sorted_configs(os.path.join(ROOT, 'src'), cfgs)
    print_cfgs(cfgs)


def print_defaults():
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cfgs = get_defaults(os.path.join(ROOT, 'src/adhocracy/config/__init__.py'))
    print_cfgs(cfgs)


def print_missing():
    cfgs = configs()
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    get_sorted_configs(os.path.join(ROOT, 'src'), cfgs)
    defaults = get_defaults(os.path.join(ROOT,
                            'src/adhocracy/config/__init__.py'))
    for key in sorted(cfgs.confs.keys()):
        miss = True
        for key2 in sorted(defaults.confs.keys()):
            if key == key2:
                miss = False
        if miss:
            print(key)


def print_obsolete():
    cfgs = configs()
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    get_sorted_configs(os.path.join(ROOT, 'src'), cfgs)
    defaults = get_defaults(os.path.join(ROOT,
                            'src/adhocracy/config/__init__.py'))
    for key in sorted(defaults.confs.keys()):
        miss = True
        for key2 in sorted(cfgs.confs.keys()):
            if key == key2:
                miss = False
        if miss:
            print(key)


def main():
    used = configs()
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    SRC = os.path.join(ROOT, 'src')
    get_sorted_configs(SRC, used)
    defaults = get_defaults(os.path.join(SRC, 'adhocracy/config/__init__.py'))

    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-u", "--used", action="store_true",
                       help="print used options in code")
    group.add_argument("-d", "--default", action="store_true",
                       help="print default options in __init__.py")
    parser.add_argument("-D", "--difference", action="store_true",
                        help="print the difference between used and "
                        "default options")
    parser.add_argument("-p", "--packages", action="store_true",
                        help="get packages of used options")
    parser.add_argument("-i", "--imports", action="store_true",
                        help="check for import config from pylons")

    args = parser.parse_args()

    if args.used:
        if args.difference:
            print_cfgs(used, defaults)
        else:
            print_cfgs(used)
    if args.default:
        if args.difference:
            print_cfgs(defaults, used)
        else:
            print_cfgs(defaults)
    if args.packages:
        for key in sorted(used.confs.keys()):
                print(key),
                print(": "),
                for conf in used.confs[key]:
                    print("!\\"),
                    print(conf.get_package()),
                    print("/!"),
                    print(conf.typ),
                    None
                print("")
    if args.imports:
        for f in get_pylons_imports(SRC):
            print(f)


if __name__ == '__main__':
    main()

