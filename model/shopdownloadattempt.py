from datetime import date

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import Column, Integer, String, Unicode, DateTime, Boolean, ForeignKey, Float
from sqlalchemy.databases import postgres

from scatterbrainz.model.meta import metadata

PGUuid = postgres.PGUuid
Base = declarative_base(metadata=metadata)
class ShopDownloadAttempt(Base):

    __tablename__ = 'scatterbrainz_downloadattempt'
    
    mbid = Column(u'release_group_mbid', PGUuid(), ForeignKey('release_group.gid'), nullable=False, primary_key=True)
    gotsearchresults = Column(u'got_search_results', Boolean(), nullable=False)
    tried = Column(u'date', DateTime(), nullable=False)
    error = Column(u'error', Unicode())

    def __init__(self, mbid, tried, gotsearchresults, error=None):
        self.mbid = mbid
        self.tried = tried
        self.gotsearchresults = gotsearchresults
        self.error = error

