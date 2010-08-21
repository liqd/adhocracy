from __future__ import with_statement
import os
from fabric.api import *
from fabric.contrib.console import confirm

env.hosts = ['liqd.net']
env.user = 'liqdnet'
env.deploy_dir = '/home/%s/' % env.user

def deploy():
    put('pip-requirements.txt', env.deploy_dir)
    with cd(env.deploy_dir):
        #run('virtualenv .')
        run('source bin/activate')
        #run('easy_install pip')
        run('bin/pip install -E . -r pip-requirements.txt')
        with cd('src/adhocracy/docs'):
            run('make html')
        run('touch site.wsgi')
