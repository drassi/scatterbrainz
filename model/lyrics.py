from datetime import date

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import Column, Integer, String, Unicode, DateTime, Boolean, ForeignKey
from sqlalchemy.databases import postgres

from scatterbrainz.model.meta import metadata

PGUuid = postgres.PGUuid
Base = declarative_base(metadata=metadata)
class Lyrics(Base):

    __tablename__ = 'scatterbrainz_lyrics'
    
    mbid = Column(u'recording_mbid', PGUuid(), ForeignKey('recording.gid'), nullable=False, primary_key=True)
    lyrics = Column(u'lyrics', Unicode(), nullable=False)
    original_url = Column(u'original_url', Unicode(), nullable=False)
    updated = Column(u'added', DateTime(), nullable=False)

    def __init__(self, mbid, lyrics, original_url, updated):
        self.mbid = mbid
        self.lyrics = lyrics
        self.original_url = original_url
        self.updated = updated
    
