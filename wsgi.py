#!/usr/bin/env python


def application(environ, start_response):

    ctype = 'text/html'
    response_body = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">
<title>Welcome to OpenShift</title>
</head>
<body>
badges
</body>
</html>'''
    response_body = response_body.encode('utf-8')

    status = '200 OK'
    response_headers = [
        ('Content-Type', ctype),
        ('Content-Length', str(len(response_body))),
    ]
    start_response(status, response_headers)
    return [response_body, ]

#
# Below for testing only
#
if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    httpd = make_server('localhost', 8051, application)
    # Wait for a single request, serve it and quit.
    httpd.handle_request()
