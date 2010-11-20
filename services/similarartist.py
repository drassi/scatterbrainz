import logging
from datetime import datetime

from scatterbrainz.lib.pylast import WSError

from scatterbrainz.model.similarartist import SimilarArtist
from scatterbrainz.model.musicbrainz import MBArtist

log = logging.getLogger(__name__)

def get_similar_artists(Session, lastfmNetwork, artist):
    mbid = artist.mbid
    similarmbids = map(lambda x: x.similar_artist_mbid, Session.query(SimilarArtist).filter_by(artist_mbid=mbid).all())
    if not similarmbids:
        Session.begin()
        now = datetime.now()
        log.info('Hitting last.fm similar artists for ' + artist.name + ' ' + mbid)
        dummyArtist = lastfmNetwork.get_artist('')
        try:
            similarlastfm = dummyArtist.get_similar_by_mbid(artist.mbid)
        except WSError, e:
            log.warn('Got last.fm WSError [' + e.details + '] retrying with string name')
            similarlastfm = lastfmNetwork.get_artist(artist.name).get_similar()
        similarmbidtomatch = {}
        for lastfmartist in similarlastfm:
            if lastfmartist.mbid is not None:
                similarmbidtomatch[lastfmartist.mbid] = lastfmartist.match
        if not similarmbidtomatch:
            log.warn('No similar artists found for ' + artist.name + ' ' + artist.gid)
        similarmbids = similarmbidtomatch.keys()
        for similarmbid in similarmbids:
            similarartist = Session.query(MBArtist).filter_by(gid=similarmbid).first()
            if similarartist:
                Session.add(SimilarArtist(unicode(mbid), unicode(similarmbid), similarmbidtomatch[similarmbid], now))
            else:
                log.warn('Couldnt find similar artist ' + similarmbid + ' in artists table!')
        Session.commit()
    
    return similarmbids

