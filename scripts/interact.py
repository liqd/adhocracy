"""uwsgi development helpers: open interactive python shells"""
import os
import sys
import inspect
import code


class RestoredStandardInputContext(object):

    def __enter__(self):
        self.backup_stdin = os.dup(sys.stdin.fileno())
        os.dup2(sys.stdout.fileno(), sys.stdin.fileno())

    def __exit__(self, error_type, error, traceback):
        os.dup2(self.backup_stdin, sys.stdin.fileno())


def interact(locals=None, plain=False):

    with RestoredStandardInputContext():
        code.interact(local=locals or inspect.currentframe().f_back.f_locals)


def interact_ipdb():

    with RestoredStandardInputContext():
        import ipdb
        ipdb.set_trace()

__builtins__['PDB'] = interact
__builtins__['IPDB'] = interact_ipdb
