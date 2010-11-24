import logging
from datetime import datetime

from scatterbrainz.lib.pylast import WSError

from scatterbrainz.model.similarartist import SimilarArtist
from scatterbrainz.model.musicbrainz import *

log = logging.getLogger(__name__)

def get_similar_artists(Session, lastfmNetwork, mbartist):
    mbid = mbartist.gid
    similarmbids = map(lambda x: x.similar_artist_mbid, Session.query(SimilarArtist).filter_by(artist_mbid=mbid).all())
    if not similarmbids:
        Session.begin()
        now = datetime.now()
        log.info('Hitting last.fm similar artists for ' + mbid)
        dummyArtist = lastfmNetwork.get_artist('')
        try:
            similarlastfm = dummyArtist.get_similar_by_mbid(mbid)
        except WSError, e:
            artistName = Session.query(MBArtistName.name).join(MBArtist.name).filter(MBArtist.gid==mbid).one()[0]
            log.warn('Got last.fm WSError [' + e.details + '] retrying with string name ' + artistName)
            similarlastfm = lastfmNetwork.get_artist(artistName).get_similar()
        similarmbidtomatch = {}
        for lastfmartist in similarlastfm:
            if lastfmartist.mbid is not None:
                similarmbidtomatch[lastfmartist.mbid] = lastfmartist.match
        if not similarmbidtomatch:
            log.warn('No similar artists found for ' + mbid)
        similarmbids = similarmbidtomatch.keys()
        for similarmbid in similarmbids:
            similarartist = Session.query(MBArtist).filter_by(gid=similarmbid).first()
            if similarartist:
                Session.add(SimilarArtist(unicode(mbid), unicode(similarmbid), similarmbidtomatch[similarmbid], now))
            else:
                log.warn('Couldnt find similar artist ' + similarmbid + ' in artists table!')
        Session.commit()
    
    return map(unicode, similarmbids)

