import sys
import time
import logging
import xmlrpclib
import threading
import traceback

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
                        except:
                            exc_type, exc_value, exc_traceback = sys.exc_info()
                            importtrace = repr(traceback.format_exception(exc_type, exc_value, exc_traceback))
                            log.error('[shop worker] caught exception in loop ' + importtrace)
                            Session.rollback()
                            Session.begin()
                            download.failedimport = True
                            download.importtrace = importtrace
                            Session.commit()
            except Exception as e:
                log.error('[shop worker] caught exception out of loop ' + repr(e))
                Session.rollback()
            if pendingdownloads:
                time.sleep(10)
            else:
                time.sleep(60)

def start_shopworker():
    worker = ShopWorkerThread()
    worker.start()

