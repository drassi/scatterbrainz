import logging
from datetime import datetime

from scatterbrainz.services import wikipedia

from scatterbrainz.model.artistbio import ArtistBio

log = logging.getLogger(__name__)

def get_artist_bio(Session, artistMbid, wikiURL):
    bio = Session.query(ArtistBio).filter_by(mbid=artistMbid).first()
    if bio:
        return bio.bio
    else:
        try:
            Session.begin()
            html, fishy = wikipedia.get_summary(wikiURL)
            html = unicode(html)
            bio = ArtistBio(artistMbid, html, unicode(wikiURL), fishy, datetime.now())
            Session.add(bio)
            Session.commit()
            return html
        except Exception, e:
            log.error('is wikipedia down for everyone or just me? ' + e.__repr__())
            return ''

