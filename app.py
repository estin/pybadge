#!/usr/bin/python
import os
import sys
import cherrypy

# hack to make sure we can load wsgi.py as a module in this class
sys.path.insert(0, os.path.dirname(__file__))

# if run at openshift - activate virtualenv
if 'OPENSHIFT_PYTHON_DIR' in os.environ:
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


# Get the environment information we need to start the server
IP = os.environ.get('OPENSHIFT_PYTHON_IP', '127.0.0.1')
PORT = int(os.environ.get('OPENSHIFT_PYTHON_PORT', 5000))
HOST_NAME = os.environ.get('OPENSHIFT_GEAR_DNS', 'localhost')


# Configure cherrypy server
cherrypy.config.update({
    'server.socket_host': IP,
    'server.socket_port': PORT,
})


# application
import time
import json
import urllib.request

CACHE_TTL = 5 * 60
PYPI_URL_TMPL = 'https://pypi.python.org/pypi/{}/json'
SHIELDS_URL_TMPL = 'https://img.shields.io/badge/{}-{}-{}.{}'
FIELDS_MAP = {
    'version': lambda d: d['info']['version'],

    'downloads': lambda d: d['info']['downloads']['last_month'],

    'format': lambda d: d['releases'][d['info']['version']][0]['packagetype']
}


class Cache(object):
    STORAGE = {}

    @classmethod
    def set(cls, key, value, ttl=None):
        cls.STORAGE[key] = {
            "expired": time.time() + ttl,
            "value": value
        }

    @classmethod
    def get(cls, key):
        item = cls.STORAGE.get(key)
        if item:
            # remove expired value
            if item['expired'] < time.time():
                del cls.STORAGE[key]
                return
            return item['value']


@cherrypy.popargs('project', 'field')
class Badge(object):

    def _get_json_from_pypi(self, project):

        # check cache
        data = Cache.get(project)
        if data:
            return data

        # fetch data from pypi
        with urllib.request.urlopen(PYPI_URL_TMPL.format(project)) as response:
            raw_data = json.loads(response.read().decode())

        # fetch values from data
        data = dict(
            (key, getter(raw_data)) for key, getter in FIELDS_MAP.items()
        )

        # save in cache
        Cache.set(project, data, ttl=CACHE_TTL)

        return data

    def _get_shields_url(
            self, project, field, label=None, color=None, frmt=None):
        data = self._get_json_from_pypi(project)
        return SHIELDS_URL_TMPL.format(
            label or field,
            data[field],  # get field value
            color or 'green',
            frmt or 'svg',
        )

    @cherrypy.expose
    def index(self, project, field, label=None, color=None, frmt=None):
        if field not in FIELDS_MAP:
            raise cherrypy.HTTPError(400, 'Invalid field %s' % field)

        raise cherrypy.HTTPRedirect(
            self._get_shields_url(project, field, label, color, frmt)
        )


class Main(object):

    def __init__(self):
        self.badge = Badge()

    @cherrypy.expose
    def index(self):
        badges = [
            "<li><img src=\"http://{}:{}/badge/pomp/{}\"></li>".format(
                HOST_NAME,
                80 if 'OPENSHIFT_PYTHON_DIR' in os.environ else PORT,
                field,
            ) for field in FIELDS_MAP
        ]
        return 'Pomp pypi status: <ul>%s</ul>' % ''.join(badges)

if __name__ == '__main__':
    cherrypy.quickstart(Main())
