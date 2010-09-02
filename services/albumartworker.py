import time
import logging
import threading

from datetime import datetime, timedelta

from scatterbrainz.model.meta import Session
from scatterbrainz.model.album import Album

from scatterbrainz.services import albumart

from sqlalchemy import or_

log = logging.getLogger(__name__)

class AlbumArtWorkerThread(threading.Thread):
    def run(self):
        print 'Starting album art worker...'
        while True:
            album = Session.query(Album).filter(Album.albumArtFilename == None).filter(or_(Album.lastHitAlbumArtExchange < datetime.now() - timedelta(days=30), Album.lastHitAlbumArtExchange == None)).order_by(Album.lastHitAlbumArtExchange).first()
            if album is not None:
                log.info('[album art worker] looking up album art for ' + album.name)
                albumart.get_art(Session, album)
                time.sleep(360)
            else:
                time.sleep(1800)

def start_albumartworker():
    worker = AlbumArtWorkerThread()
    worker.start()

