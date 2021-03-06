# -*- coding: utf-8 -*-
"""
This plugin adds support for :class:`werkzeug.Response`, all kinds of
:exc:`werkzeug.exceptions` and provides a thread-local instance of
:class:`werkzeug.Request`. It basically turns Bottle into Flask.

The plugin instance doubles as a werkzeug module object, so you don't need to
import werkzeug in your application.

For werkzeug library documentation, see: http://werkzeug.pocoo.org/

Example::

    import bottle

    app = bottle.Bottle()
    werkzeug = bottle.ext.werkzeug.Plugin()
    app.install(werkzeug)

    req = werkzueg.request # For the lazy.

    @app.route('/hello/:name')
    def say_hello(name):
        greet = {'en':'Hello', 'de':'Hallo', 'fr':'Bonjour'}
        language = req.accept_languages.best_match(greet.keys())
        if language:
            return werkzeug.Response('%s %s!' % (greet[language], name))
        else:
            raise werkzeug.exceptions.NotAcceptable()

"""
import sys
import werkzeug
from werkzeug import *
import bottle


class WerkzeugDebugger(DebuggedApplication):
    """ A subclass of :class:`werkzeug.debug.DebuggedApplication` that obeys the
        :data:`bottle.DEBUG` setting. """

    def __call__(self, environ, start_response):
        if bottle.DEBUG:
            return DebuggedApplication.__call__(self, environ, start_response)
        return self.app(environ, start_response)


class WerkzeugPlugin(object):
    """ This plugin adds support for :class:`werkzeug.Response`, all kinds of
        :module:`werkzeug.exceptions` and provides a thread-local instance of
        :class:`werkzeug.Request`. It basically turns Bottle into Flask. """

    name = 'werkzeug'
    api = 2

    def __init__(self, evalex=False, request_class=werkzeug.Request,
                       response_class=werkzeug.Response, debugger_class=WerkzeugDebugger):
        self.request_class = request_class
        self.response_class = response_class
        self.debugger_class = debugger_class
        self.evalex=evalex
        self.app = None

    def setup(self, app):
        self.app = app
        if self.debugger_class:
            app.wsgi = self.debugger_class(app.wsgi, evalex=self.evalex)
            app.catchall = False

    def apply(self, callback, context):
        def wrapper(*a, **ka):
            environ = bottle.request.environ
            bottle.local.werkzeug_request = self.request_class(environ)
            bottle.local.werkzeug_response = self.response_class(environ)
            try:
                rv = callback(*a, **ka)
            except werkzeug.exceptions.HTTPException:
                rv = sys.exc_info()[1]
            if isinstance(rv, werkzeug.BaseResponse):
                rv = bottle.HTTPResponse(rv.iter_encoded(), rv.status_code, rv.headers)
            return rv
        return wrapper

    @property
    def request(self):
        ''' Return a local proxy to the current :class:`werkzeug.Request`
            instance.'''
        return werkzeug.LocalProxy(lambda: bottle.local.werkzeug_request)

    @property
    def response(self):
        ''' Return a local proxy to the current :class:`werkzeug.Response`
            instance.'''
        return werkzeug.LocalProxy(lambda: bottle.local.werkzeug_response)

    def __getattr__(self, name):
        ''' Convenient access to werkzeug module contents. '''
        return getattr(werkzeug, name)


Plugin = WerkzeugPlugin
