from datetime import datetime

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import Column, Integer, String, Unicode, DateTime, Boolean, ForeignKey, Float
from sqlalchemy.databases import postgres

from scatterbrainz.model.meta import metadata

PGUuid = postgres.PGUuid
Base = declarative_base(metadata=metadata)
class ShopDownload(Base):

    __tablename__ = 'scatterbrainz_downloads'
    
    infohash = Column(u'infohash', Unicode(), nullable=False, primary_key=True)
    release_mbid = Column(u'release_mbid', PGUuid(), ForeignKey('release.gid'), nullable=False)
    release_group_mbid = Column(u'release_group_mbid', PGUuid(), ForeignKey('release_group.gid'), nullable=False)
    torrent_url = Column(u'torrent_url', Unicode(), nullable=False)
    torrent_page_url = Column(u'torrent_page_url', Unicode(), nullable=False)
    torrent_id = Column(u'torrent_id', Unicode(), nullable=False)
    num_seeders = Column(u'num_seeders', Integer(), nullable=False)
    file_json = Column(u'file_json', Unicode(), nullable=False)
    started = Column(u'started', DateTime(), nullable=False)
    finished = Column(u'finished', DateTime())
    isdone = Column(u'is_done', Boolean(), nullable=False)
    failedimport = Column(u'failed_import', Boolean(), nullable=False)
    importtrace = Column(u'import_trace', Unicode(), nullable=True)
    minscore = Column(u'min_score', Float(), nullable=False)
    avgscore = Column(u'avg_score', Float(), nullable=False)
    owner_id = Column(u'owner_id', Integer(), ForeignKey('scatterbrainz_user.user_id'), nullable=False)

    def __init__(self, release_mbid, release_group_mbid, infohash, torrent_url, torrent_page_url, torrent_id, num_seeders, file_json, minscore, avgscore, owner_id):
        self.release_mbid = release_mbid
        self.release_group_mbid = release_group_mbid
        self.infohash = unicode(infohash)
        self.torrent_url = unicode(torrent_url)
        self.torrent_page_url = unicode(torrent_page_url)
        self.torrent_id = unicode(torrent_id)
        self.num_seeders = num_seeders
        self.file_json = unicode(file_json)
        self.minscore = minscore
        self.avgscore = avgscore
        self.owner_id = owner_id
        self.started = datetime.now()
        self.finished = None
        self.isdone = False
        self.failedimport = False
        self.importtrace = None
        self.owner_id = owner_id

