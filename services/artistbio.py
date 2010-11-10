from datetime import datetime

from scatterbrainz.services import wikipedia

from scatterbrainz.model.artistbio import ArtistBio

def get_artist_bio(Session, artistMbid, wikiURL):
    bio = Session.query(ArtistBio).filter_by(mbid=artistMbid).first()
    if bio:
        return bio.bio
    else:
        Session.begin()
        html = unicode(wikipedia.get_summary(wikiURL))
        bio = ArtistBio(artistMbid, html, wikiURL, datetime.now())
        Session.add(bio)
        Session.commit()
        return html
    
