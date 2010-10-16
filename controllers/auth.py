from pylons import request, tmpl_context as c

from scatterbrainz.lib.base import BaseController, render

class AuthController(BaseController):

    def login(self):
        return render('login.html')

