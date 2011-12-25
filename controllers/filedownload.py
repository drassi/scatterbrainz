import logging

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from scatterbrainz.lib.base import BaseController, render

log = logging.getLogger(__name__)

class FiledownloadController(BaseController):

    def album(self):
        mbid = request.params['mbid']

    def track(self):
        mbid = request.params['mbid']

