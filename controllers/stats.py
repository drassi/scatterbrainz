import random
import string
import logging
import simplejson
from operator import itemgetter
from datetime import datetime, timedelta

from sqlalchemy import distinct
from sqlalchemy import func
from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from scatterbrainz.lib.base import BaseController, render

from scatterbrainz.model import User, Group, Permission, Invite

log = logging.getLogger(__name__)

from repoze.what.predicates import has_permission
from repoze.what.plugins.pylonshq import ActionProtector
from scatterbrainz.model.meta import Session
from scatterbrainz.model import TrackPlay

class StatsController(BaseController):

    @ActionProtector(has_permission('admin'))
    def index(self):
        c.playsEver, c.ipsEver = Session.query(func.count(TrackPlay.id), func.count(distinct(TrackPlay.ip))).one()
        c.plays7d, c.ips7d = Session.query(func.count(TrackPlay.id), func.count(distinct(TrackPlay.ip))).filter(TrackPlay.timestamp > datetime.utcnow() - timedelta(days=7)).one()
        c.plays24h, c.ips24h = Session.query(func.count(TrackPlay.id), func.count(distinct(TrackPlay.ip))).filter(TrackPlay.timestamp > datetime.utcnow() - timedelta(days=1)).one()
        c.plays1h, c.ips1h = Session.query(func.count(TrackPlay.id), func.count(distinct(TrackPlay.ip))).filter(TrackPlay.timestamp > datetime.utcnow() - timedelta(hours=1)).one()
        statsEver = Session.query(User.user_name, func.count(TrackPlay.id), func.count(distinct(TrackPlay.ip))).outerjoin(TrackPlay).group_by(User.user_name).all()
        stats7d = Session.query(User.user_name, func.count(TrackPlay.id), func.count(distinct(TrackPlay.ip))).outerjoin(TrackPlay).group_by(User.user_name).filter(TrackPlay.timestamp > datetime.utcnow() - timedelta(days=7)).all()
        stats24h = Session.query(User.user_name, func.count(TrackPlay.id), func.count(distinct(TrackPlay.ip))).outerjoin(TrackPlay).group_by(User.user_name).filter(TrackPlay.timestamp > datetime.utcnow() - timedelta(days=1)).all()
        stats1h = Session.query(User.user_name, func.count(TrackPlay.id), func.count(distinct(TrackPlay.ip))).outerjoin(TrackPlay).group_by(User.user_name).filter(TrackPlay.timestamp > datetime.utcnow() - timedelta(hours=1)).all()
        stats = {}
        for uname, count, ipcount in statsEver:
            stats[uname] = {'user':uname, 'countEver':count, 'ipEver':ipcount, 'count7d':0, 'ip7d':0, 'count24h':0, 'ip24h':0, 'count1h':0, 'ip1h':0}
        for uname, count, ipcount in stats7d:
            stats[uname].update({'count7d':count, 'ip7d':ipcount})
        for uname, count, ipcount in stats24h:
            stats[uname].update({'count24h':count, 'ip24h':ipcount})
        for uname, count, ipcount in stats1h:
            stats[uname].update({'count1h':count, 'ip1h':ipcount})
        statlist = stats.values()
        statlist.sort(key=itemgetter('countEver'), reverse=True)
        c.stats = statlist
        return render('/stats.html')

