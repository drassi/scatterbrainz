import logging
from scatterbrainz.model.meta import Session
from scatterbrainz.model.auth import User
from scatterbrainz.model.scatterbrainz_ben_kv import BenKVP

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from scatterbrainz.lib.base import BaseController, render

log = logging.getLogger(__name__)

class BenKvpController(BaseController):

    def index(self):

        # Return a rendered template
        #return render('/ben_kvp.mako')
        # or, return a string
        
        return 'Hello World - how you doing today {0}'.format(Session.query(User).first())

    
    
    def makeRandom(self):
        user_name = request.environ['repoze.what.credentials']['repoze.what.userid']
        user = Session.query(User).filter(User.user_name==user_name).one()

        Session.begin()
        for i in range(10):
            info = BenKVP(owner = user,
                          key = 'random_key_{0}'.format(i),
                          value = 'random_value_{0}'.format(i))
            
            Session.add(info)
        Session.commit()

        return 'success'
                          
    def getUserKVP(self):
        user_name = request.environ['repoze.what.credentials']['repoze.what.userid']
        user = Session.query(User).filter(User.user_name==user_name).one()        
        kvp = Session.query(BenKVP).filter_by(owner = user)
        keys = [ item.key for item in kvp.all() ]
        return ';'.join([k for k in keys])
