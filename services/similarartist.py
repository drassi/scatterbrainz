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
        Session.begin()
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
        similarartists = []
        for similarmbid in similarmbidtomatch.keys():
            similarartist = Session.query(MBArtist).filter_by(gid=similarmbid).first()
            if similarartist:
                similarartists.append(SimilarArtist(unicode(mbid), unicode(similarmbid), similarmbidtomatch[similarmbid], now))
            else:
                log.warn('Couldnt find similar artist ' + similarmbid + ' in artists table!')
        Session.add_all(similarartists)
        Session.commit()
        similarartists.sort(lambda a,b: cmp(b.match, a.match))
        similarmbids = map(lambda x: x.similar_artist_mbid, similarartists)
    
    return map(unicode, similarmbids)

