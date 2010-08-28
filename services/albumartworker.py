import time
import logging
import threading

from scatterbrainz.model.meta import Session
from scatterbrainz.model.album import Album

from scatterbrainz.services import albumart

log = logging.getLogger(__name__)

class AlbumArtWorkerThread(threading.Thread):
    def run(self):
        print 'Starting album art worker...'
        while True:
            album = Session.query(Album).filter_by(albumArtFilename=None).filter_by(lastHitAlbumArtExchange=None).first()
            if album is not None:
                log.info('[album art worker] looking up album art for ' + album.name)
                albumart.get_art(Session, album)
                time.sleep(360)
            else:
                time.sleep(1800)

def start_albumartworker():
    worker = AlbumArtWorkerThread()
    worker.start()

