from datetime import date

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import Column, Integer, String, Unicode, DateTime, Boolean, ForeignKey
from sqlalchemy.databases.postgres import PGUuid

from scatterbrainz.model.meta import metadata

Base = declarative_base(metadata=metadata)
class ArtistBio(Base):

    __tablename__ = 'scatterbrainz_artistbio'
    
    mbid = Column(u'artist_mbid', PGUuid(), ForeignKey('artist.gid'), primary_key=True)
    bio = Column(u'bio', Unicode(), nullable=False)
    original_url = Column(u'original_url', Unicode(), nullable=False)
    fishy = Column(u'fishy', Boolean(), nullable=False)
    updated = Column(u'added', DateTime(), nullable=False)

    def __init__(self, mbid, bio, original_url, fishy, updated):
        self.mbid = mbid
        self.bio = bio
        self.original_url = original_url
        self.fishy = fishy
        self.updated = updated

