#!/usr/bin/python
import cherrypy

import settings
import badge


# Configure cherrypy server
cherrypy.config.update({
    'server.socket_host': settings.IP,
    'server.socket_port': settings.PORT,
})


if __name__ == '__main__':
    cherrypy.quickstart(badge.Main())
