import random
import string
import logging
import simplejson
from datetime import datetime

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from scatterbrainz.lib.base import BaseController, render

from scatterbrainz.model import User, Group, Permission, Invite

log = logging.getLogger(__name__)

from repoze.what.predicates import has_permission
from repoze.what.plugins.pylonshq import ActionProtector
from scatterbrainz.model.meta import Session

class RegisterController(BaseController):

    @ActionProtector(has_permission('admin'))
    def invite(self):
        if request.POST:
            who = request.params['who']
            c.code = ''.join(random.choice(string.letters + string.digits) for i in xrange(32))
            invite = Invite(who, c.code)
            Session.begin()
            Session.add(invite)
            Session.commit()
            return render('/display-invite.html')
        else:
            return render('/create-invite.html')

    def register(self, code):
        invite = Session.query(Invite).filter_by(code=code).first()
        if invite is None:
            return 'Your registration code appears to be invalid.'
        c.code = code
        return render('/register.html')
    
    def create(self):
        usr = request.params['login']
        if Session.query(User).filter_by(user_name=usr).count() > 0:
            return simplejson.dumps({'success':False,'msg':'That username is already taken, sorry.'})
        pwd = request.params['pass']
        if len(usr) < 3 or len(pwd) < 3:
            return simplejson.dumps({'success':False,'msg':'Your username and password must each be at least 3 characters.'})
        code = request.params['code']
        invite = Session.query(Invite).filter_by(code=code).first()
        if invite is None:
            return simplejson.dumps({'success':False,'msg':'Your registration code appears to be invalid.'})
        user = User()
        user.who = invite.who
        user.user_name = usr
        user.password = pwd
        user.registered = datetime.now()
        Session.begin()
        user.groups = [Session.query(Group).filter_by(group_name='users').one()]
        Session.delete(invite)
        Session.add(user)
        Session.commit()
        return simplejson.dumps({'success':True})
    
