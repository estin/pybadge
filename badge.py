import json
import time
import asyncio

import wand.image
import aiohttp
import settings


FIELDS_MAP = {
    'version': lambda d: d['info']['version'],

    'downloads': lambda d: d['info']['downloads']['last_month'],

    'format': lambda d: d['releases'][d['info']['version']][0]['packagetype']
}


# stolen from schields.io
SVG_TMPL = """
<svg xmlns="http://www.w3.org/2000/svg" width="88" height="20">
    <linearGradient id="b" x2="0" y2="100%">
        <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
        <stop offset="1" stop-opacity=".1"/>
    </linearGradient>
    <mask id="a">
        <rect width="88" height="20" rx="3" fill="#fff"/>
    </mask>
    <g mask="url(#a)">
        <path fill="#555" d="M0 0h44v20H0z"/>
        <path fill="#4c1" d="M44 0h44v20H44z"/>
        <path fill="url(#b)" d="M0 0h88v20H0z"/>
    </g>
    <g fill="#fff"
            text-anchor="middle"
            font-family="DejaVu Sans,Verdana,Geneva,sans-serif"
            font-size="11">
        <text x="22" y="15" fill="#010101" fill-opacity=".3">{key}</text>
        <text x="22" y="14">{key}</text>
        <text x="65" y="15" fill="#010101" fill-opacity=".3">{value}</text>
        <text x="65" y="14">{value}</text>
    </g>
</svg>
"""


# TODO cleanup cache
class Cache(object):
    STORAGE = {}

    @classmethod
    def check(cls):
        # build new cache only with actual items
        now = time.time()
        cls.STORAGE = dict(
            (k, v) for k, v in cls.STORAGE.items() if v['expired'] < now
        )

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

    @classmethod
    def update(cls, key, params):
        if key not in cls.STORAGE:
            raise RuntimeError("Cache empty for %s" % key)
        cls.STORAGE[key].update(params)


@asyncio.coroutine
def fetch_url(url, method=None):
    response = yield from aiohttp.request(method or 'GET', url)
    return (yield from response.read()).decode()


@asyncio.coroutine
def get_json_from_pypi(cache_key, project):

    # check cache
    data = Cache.get(cache_key)
    if data:
        return data

    # fetch data from pypi
    raw_data = json.loads(
        (yield from fetch_url(settings.PYPI_URL_TMPL.format(project)))
    )

    # fetch values from data
    data = dict(
        (key, getter(raw_data)) for key, getter in FIELDS_MAP.items()
    )

    # save in cache
    Cache.set(cache_key, data, ttl=settings.CACHE_TTL)

    return data


def build_svg(cache_key, key, value):
    # build svg
    svg = SVG_TMPL.format(key=key, value=value).encode()

    # save svg in cache
    Cache.update(cache_key, {
        'svg': svg
    })

    return svg


def build_png(cache_key, svg):
    # convert
    with wand.image.Image(blob=svg, format="svg") as image:
        png = image.make_blob("png")

        # save png in cache
        Cache.update(cache_key, {
            'png': png
        })

        return png


@asyncio.coroutine
def handle(request):

    service = request.match_info.get('service', None)
    project = request.match_info.get('project', None)
    field = request.match_info.get('field', None)
    format = request.match_info.get('format', None)

    # project cache correspond to service
    cache_key = service + '-' + project

    # get data from cache or from pypi
    data = yield from get_json_from_pypi(cache_key, project)

    # get svg from cache or build it
    svg = data.get('svg', build_svg(cache_key, field, data[field]))

    if format == 'svg':
        return aiohttp.web.Response(
            body=svg,
            content_type='image/svg+xml;charset=utf-8',
        )
    elif format == 'png':
        # get png from cache or build it by svg
        png = data.get('png', build_png(cache_key, svg))
        return aiohttp.web.Response(
            body=png,
            content_type='image/png',
        )


def clear_cache(loop):
    Cache.check()
    loop.call_later(settings.CACHE_TTL, clear_cache, loop)
