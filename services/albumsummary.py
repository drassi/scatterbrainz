import logging
from datetime import datetime

from scatterbrainz.services import wikipedia

from scatterbrainz.model.albumsummary import AlbumSummary

log = logging.getLogger(__name__)

def get_album_summary(Session, albumMbid, wikiURL):
    summary = Session.query(AlbumSummary).filter_by(mbid=albumMbid).first()
    if summary:
        return summary.summary
    else:
        try:
            Session.begin()
            html, fishy = wikipedia.get_summary(wikiURL)
            html = unicode(html)
            summary = AlbumSummary(albumMbid, html, unicode(wikiURL), fishy, datetime.now())
            Session.add(summary)
            Session.commit()
            return html
        except Exception, e:
            log.error('is wikipedia down for everyone or just me? ' + e.__repr__())
            return ''

