import os
import sys

# hack to make sure we can load wsgi.py as a module in this class
sys.path.insert(0, os.path.dirname(__file__))

IS_OPENSHIFT = 'OPENSHIFT_PYTHON_DIR' in os.environ

# Get the environment information we need to start the server
IP = os.environ.get('OPENSHIFT_PYTHON_IP', '127.0.0.1')
PORT = int(os.environ.get('OPENSHIFT_PYTHON_PORT', 5001))
HOST_NAME = os.environ.get('OPENSHIFT_GEAR_DNS', 'localhost')

CACHE_TTL = 5 * 60
PYPI_URL_TMPL = 'https://pypi.python.org/pypi/{}/json'

# if run at openshift - activate virtualenv
if IS_OPENSHIFT:
    virtenv = os.environ['OPENSHIFT_PYTHON_DIR'] + '/virtenv/'
    virtualenv = os.path.join(virtenv, 'bin/activate_this.py')
    try:
        # Multi-Line for Python v3.3:
        exec_namespace = dict(__file__=virtualenv)
        with open(virtualenv, 'rb') as exec_file:
            file_contents = exec_file.read()
        compiled_code = compile(file_contents, virtualenv, 'exec')
        exec(compiled_code, exec_namespace)
    except IOError:
        pass
