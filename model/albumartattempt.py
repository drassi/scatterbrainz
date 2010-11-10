from datetime import date

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import Column, Integer, String, Unicode, DateTime, Boolean, ForeignKey
from sqlalchemy.databases.postgres import PGUuid

from scatterbrainz.model.meta import metadata

Base = declarative_base(metadata=metadata)
class AlbumArtAttempt(Base):

    __tablename__ = 'scatterbrainz_albumartattempt'
    
    mbid = Column(u'release_group_mbid', PGUuid(), ForeignKey('release_group.gid'), nullable=False, primary_key=True)
    tried = Column(u'added', DateTime(), nullable=False)
    error = Column(u'error', Unicode())

    def __init__(self, mbid, tried, error=None):
        self.mbid = mbid
        self.tried = tried
        self.error = error
    
