import os, sys
sys.path.append('/opt/adhocracy')
os.environ['PYTHON_EGG_CACHE'] = '/opt/adhocracy/data/eggs'

from paste.deploy import loadapp

application = loadapp('config:/opt/adhocracy/example.ini')
