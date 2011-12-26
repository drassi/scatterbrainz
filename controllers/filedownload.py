import os
import time
import zipfile
import logging
import tempfile

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from scatterbrainz.lib.base import BaseController, render

from scatterbrainz.config.config import Config

from scatterbrainz.model.meta import Session
from scatterbrainz.model.musicbrainz import *
from scatterbrainz.model.album import Album

log = logging.getLogger(__name__)

class FiledownloadController(BaseController):

    def album(self):
        mbid = request.params['mbid']
        album = Session.query(Album).filter_by(mbid=mbid).one()
        albumname = album.name
        artistname = album.artistcredit
        tracks = album.tracks
        exportdir = Config.MUSIC_PATH + '../export'
        zipname = artistname + ' - ' + albumname + '.zip'
        zippath = exportdir + '/' + zipname
        z = zipfile.ZipFile(zippath, 'w', zipfile.ZIP_STORED)
        multidisc = max([track.discnum for track in tracks]) > 1
        for track in tracks:
            realpath = Config.MUSIC_PATH + track.file.filepath
            filename = '%02d. %s' % (track.tracknum, track.name)
            if multidisc:
                filename = track.disc + '-' + filename
            z.write(realpath, filename)
        z.close()
        return redirect('/export/' + zipname)

    def track(self):
        mbid = request.params['mbid']

