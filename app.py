#!/usr/bin/python
import asyncio
from aiohttp import web

import settings
import badge


@asyncio.coroutine
def handle_index(request):
    badges = [
        "<li><img src=\"http://{host}:{port}/pypi/{field}/pomp.svg\"><img src=\"http://{host}:{port}/pypi/{field}/pomp.png\"></li>".format(
            host=settings.HOST_NAME,
            port=80 if settings.IS_OPENSHIFT else settings.PORT,
            field=field,
        ) for field in badge.FIELDS_MAP
    ]
    return web.Response(
        content_type='text/html; charset=utf-8',
        body=('Pomp pypi status: <ul>%s</ul>' % ''.join(badges)).encode(),
    )


@asyncio.coroutine
def init(loop):
    app = web.Application(loop=loop)

    app.router.add_route('GET', '/', handle_index)
    app.router.add_route(
        'GET', '/{service}/{field}/{project}.{format}', badge.handle
    )

    srv = yield from loop.create_server(
        app.make_handler(), settings.IP, settings.PORT,
    )

    if not settings.IS_OPENSHIFT:
        print("Server started at http://%s:%s" % (settings.IP, settings.PORT))

    return srv


if __name__ == '__main__':

    loop = asyncio.get_event_loop()
    loop.run_until_complete(init(loop))

    # clear cache each settings.CACHE_TTL seconds
    loop.call_later(settings.CACHE_TTL, badge.clear_cache, loop)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
