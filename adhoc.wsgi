import os, sys
sys.path.append('/home/fl/web/adhocracy.cc')
os.environ['PYTHON_EGG_CACHE'] = '/home/fl/web/adhocracy.cc/data/eggs'

from paste.deploy import loadapp

application = loadapp('config:/home/fl/web/adhocracy.cc/deploy.ini')
