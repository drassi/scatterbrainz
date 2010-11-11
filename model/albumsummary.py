from datetime import date

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import Column, Integer, String, Unicode, DateTime, Boolean, ForeignKey
from sqlalchemy.databases.postgres import PGUuid

from scatterbrainz.model.meta import metadata

Base = declarative_base(metadata=metadata)
class AlbumSummary(Base):

    __tablename__ = 'scatterbrainz_albumsummary'
    
    mbid = Column(u'release_group_mbid', PGUuid(), ForeignKey('release_group.gid'), primary_key=True)
    summary = Column(u'summary', Unicode(), nullable=False)
    original_url = Column(u'original_url', Unicode(), nullable=False)
    fishy = Column(u'fishy', Boolean(), nullable=False)
    updated = Column(u'added', DateTime(), nullable=False)

    def __init__(self, mbid, summary, original_url, fishy, updated):
        self.mbid = mbid
        self.summary = summary
        self.original_url = original_url
        self.fishy = fishy
        self.updated = updated

