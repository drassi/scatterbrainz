from datetime import date

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import Column, Integer, String, Unicode, DateTime, Boolean, ForeignKey
from sqlalchemy.databases import postgres

from scatterbrainz.model.meta import metadata

PGUuid = postgres.PGUuid
Base = declarative_base(metadata=metadata)
class AlbumArt(Base):

    __tablename__ = 'scatterbrainz_albumart'
    
    mbid = Column(u'release_group_mbid', PGUuid(), ForeignKey('release_group.gid'), nullable=False, primary_key=True)
    path = Column(u'path', Unicode(), nullable=False)
    original_url = Column(u'original_url', Unicode(), nullable=False)
    num_results = Column(u'num_results', Integer(), nullable=False)
    updated = Column(u'added', DateTime(), nullable=False)

    def __init__(self, mbid, path, original_url, num_results, updated):
        self.mbid = mbid
        self.path = path
        self.original_url = original_url
        self.num_results = num_results
        self.updated = updated
    
