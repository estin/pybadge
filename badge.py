import time
import json
import urllib.request

import cherrypy
import settings

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
                settings.HOST_NAME,
                80 if settings.IS_OPENSHIFT else settings.PORT,
                field,
            ) for field in FIELDS_MAP
        ]
        return 'Pomp pypi status: <ul>%s</ul>' % ''.join(badges)
