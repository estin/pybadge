# pybadge
asyncio http server for generating badges

Simple alternative to [shields.io](http://shields.io/) or [pypip](https://pypip.in/)

Openshift deploy http://badges-etatarkin.rhcloud.com/

Url schema: (pybadge host)/pypi/(version|downloads|format)/(pypi project).(svg|png)

For example Django version - http://badges-etatarkin.rhcloud.com/pypi/version/django.svg

UNDER DEVELOPMENT!

TODO

* show server status on (pybadge host)/status - cache info, average time for generating svg and png
* fix svg markup depended on text length
* split server to frontend (serve request and populate cache) and backend (fetch data, generate svg and png, do not use cache)
* more informative index page
