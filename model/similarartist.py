from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import Column, Integer, String, Unicode, DateTime, ForeignKey, Float
from sqlalchemy.databases.postgres import PGUuid

from scatterbrainz.model.meta import metadata

Base = declarative_base(metadata=metadata)
class SimilarArtist(Base):

    __tablename__ = 'scatterbrainz_similarartists'
    
    artist_mbid = Column('artist_mbid', PGUuid, ForeignKey('artist.gid'), primary_key=True)
    similar_artist_mbid = Column('similar_artist_mbid', PGUuid, ForeignKey('artist.gid'), primary_key=True)
    match = Column('match', Float)
    updated = Column('updated', DateTime)

    def __init__(self, artist_mbid, similar_artist_mbid, match, now):
        self.artist_mbid = artist_mbid
        self.similar_artist_mbid = similar_artist_mbid
        self.match = match
        self.updated = now

