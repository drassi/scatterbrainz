import time
import logging
import xmlrpclib
import threading

from datetime import datetime, timedelta

from scatterbrainz.model.meta import Session
from scatterbrainz.model import ShopDownload
from scatterbrainz.config.config import Config
from scatterbrainz.services import shop as shopservice

log = logging.getLogger(__name__)

class ShopWorkerThread(threading.Thread):
    def run(self):
        pendingdownloads = False
        while True:
            try:
                downloads = Session.query(ShopDownload) \
                                   .filter(ShopDownload.isdone==False) \
                                   .filter(ShopDownload.failedimport==False) \
                                   .all()
                pendingdownloads = len(downloads) != 0
                if pendingdownloads:
                    rtorrent = xmlrpclib.ServerProxy(Config.SHOP_RPC_URL)
                    for download in downloads:
                        try:
                            infohash = download.infohash
                            iscomplete = rtorrent.d.get_complete(infohash) == 1
                            if iscomplete:
                                shopservice.importDownload(download)
                        except Exception as e:
                            log.error('[shop worker] caught exception in loop ' + e.__repr__())
                            Session.rollback()
                            Session.begin()
                            download.failedimport = True
                            Session.commit()
            except Exception as e:
                log.error('[shop worker] caught exception out of loop ' + e.__repr__())
                Session.rollback()
            if pendingdownloads:
                time.sleep(10)
            else:
                time.sleep(60)

def start_shopworker():
    worker = ShopWorkerThread()
    worker.start()

