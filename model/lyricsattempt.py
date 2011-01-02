from datetime import date

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import Column, Integer, String, Unicode, DateTime, Boolean, ForeignKey
from sqlalchemy.databases import postgres

from scatterbrainz.model.meta import metadata

PGUuid = postgres.PGUuid
Base = declarative_base(metadata=metadata)
class LyricsAttempt(Base):

    __tablename__ = 'scatterbrainz_lyricsattempt'
    
    mbid = Column(u'recording_mbid', PGUuid(), ForeignKey('recording.gid'), nullable=False, primary_key=True)
    tried = Column(u'added', DateTime(), nullable=False)
    error = Column(u'error', Unicode())

    def __init__(self, mbid, tried, error=None):
        self.mbid = mbid
        self.tried = tried
        self.error = error
    
