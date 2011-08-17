from datetime import datetime

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import relation
from sqlalchemy import Column, Integer, String, Unicode, DateTime, ForeignKey
from sqlalchemy.databases import postgres

from scatterbrainz.model.meta import metadata
from scatterbrainz.model import User

from scatterbrainz.controllers import renderer as r

PGUuid = postgres.PGUuid
Base = declarative_base(metadata=metadata)
class TrackPlay(Base):

    __tablename__ = 'scatterbrainz_trackplays'
    
    id = Column(u'id', Integer, primary_key=True)
    mbid = Column(u'track_mbid', PGUuid, ForeignKey('recording.gid'), nullable=False)
    user_id = Column(Integer, ForeignKey('scatterbrainz_user.user_id'), nullable=False)
    ip = Column(u'ip', Unicode, nullable=False)
    timestamp = Column(u'played', DateTime, nullable=False)

    user = relation(User)
    
    def __init__(self, mbid, user, ip):
        self.mbid = mbid
        self.user = user
        self.ip = ip
        self.timestamp = datetime.utcnow()

