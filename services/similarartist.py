import logging
from datetime import datetime

from sqlalchemy.sql.expression import desc

from scatterbrainz.lib.pylast import WSError

from scatterbrainz.model.similarartist import SimilarArtist
from scatterbrainz.model.musicbrainz import *

log = logging.getLogger(__name__)

def get_similar_artists(Session, lastfmNetwork, mbartist):
    mbid = mbartist.gid
    similarartists = Session.query(SimilarArtist) \
                            .filter_by(artist_mbid=mbid) \
                            .order_by(desc(SimilarArtist.match)) \
                            .all()
    similarmbids = map(lambda x: x.similar_artist_mbid, similarartists)
    if not similarmbids:
        now = datetime.now()
        log.info('Hitting last.fm similar artists for ' + mbid)
        dummyArtist = lastfmNetwork.get_artist('')
        try:
            similarlastfm = dummyArtist.get_similar_by_mbid(mbid, limit=250)
        except WSError, e:
            artistName = Session.query(MBArtistName.name).join(MBArtist.name).filter(MBArtist.gid==mbid).one()[0]
            log.warn('Got last.fm WSError [' + e.details + '] retrying with string name ' + artistName)
            similarlastfm = lastfmNetwork.get_artist(artistName).get_similar(limit=250)
        similarmbidtomatch = {}
        for lastfmartist in similarlastfm:
            if lastfmartist.mbid is not None:
                similarmbidtomatch[lastfmartist.mbid] = lastfmartist.match
        if not similarmbidtomatch:
            log.warn('No similar artists found for ' + mbid)
        similarmbids = similarmbidtomatch.keys()
        similarmbidsrecognized = set(map(lambda x: x[0], Session.query(MBArtist.gid).filter(MBArtist.gid.in_(similarmbids)).all()))
        insertmaps = []
        similarmbidsrecognizedsorted = []
        for similarmbid in similarmbids:
            if similarmbid in similarmbidsrecognized:
                insertmaps.append({
                    'artist_mbid'         : unicode(mbid),
                    'similar_artist_mbid' : unicode(similarmbid),
                    'match'               : similarmbidtomatch[similarmbid],
                    'updated'             : now
                })
                similarmbidsrecognizedsorted.append(similarmbid)
        Session.connection().execute(SimilarArtist.__table__.insert(), insertmaps)
        similarmbids = similarmbidsrecognizedsorted
    
    return map(unicode, similarmbids)

