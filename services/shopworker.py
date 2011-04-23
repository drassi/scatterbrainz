import os
import sys
import time
import logging
import xmlrpclib
import threading
import traceback
from datetime import datetime, timedelta

from sqlalchemy import select, func

from scatterbrainz.model.meta import Session
from scatterbrainz.model import ShopDownload
from scatterbrainz.config.config import Config
from scatterbrainz.services import shop as shopservice

log = logging.getLogger(__name__)

importlockid=1234

class ShopWorkerThread(threading.Thread):

    def run(self):
        
        # Only let one worker run via pg advisory lock
        acquired = Session.execute(select([func.pg_try_advisory_lock(importlockid)])).fetchone()[0]
        threadid = 'PID ' + str(os.getpid()) + ' thread ' + str(threading.current_thread())
        if acquired:
            log.info('[shop worker] %s acquired lock, starting..' % threadid)
        else:
            return
        
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
                time.sleep(30)

def start_shopworker():
    worker = ShopWorkerThread()
    worker.start()

