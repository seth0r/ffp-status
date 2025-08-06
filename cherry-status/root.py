import cherrypy
from cherrypy import HTTPError
from cherrypy._cperror import HTTPRedirect
from cherrypy.lib.static import serve_fileobj, serve_file
import jinja2
import os
import time

import modules

class Root( * modules.__classes__.values() ):
    def __init__(self):
        self.tmpdir = "/tmp"
        self.tpldir = os.path.join( os.path.dirname(os.path.realpath(__file__) ),"tpl")
        self.tplenv = jinja2.Environment( 
            loader = jinja2.FileSystemLoader( self.tpldir ),
            trim_blocks = True,
            lstrip_blocks = True
        )

    def get_tpl(self, *args):
        for t in args:
            try:
                return self.tplenv.get_template( t )
            except jinja2.exceptions.TemplateNotFound:
                pass

    def serve_site(self, tpl, **kwargs):
        lang = self.get_lang()
        kwargs.setdefault("lang", lang)
        tpl = self.get_tpl( tpl, "%s.%s.html" % (tpl, lang), "%s.html" % tpl )
        if tpl is not None:
            return tpl.render( me = self, **kwargs )
        raise HTTPError(404,"Template not found.")

    def get_lang(self):
        user = None
        if hasattr(self,"get_user"):
            user = self.get_user()
        if user and user.settings and "lang" in user.settings:
            return user.settings["lang"]
        else:
            return cherrypy.request.headers.get("Accept-Language","en")[:2]

    @cherrypy.expose
    def default(self,name):
        return self.serve_site( name )

