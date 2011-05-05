from datetime import datetime

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import orm
from sqlalchemy import Column, Integer, String, Unicode, DateTime, Boolean, ForeignKey
from sqlalchemy.databases import postgres
from sqlalchemy.ext.orderinglist import ordering_list

from scatterbrainz.model.meta import metadata
from scatterbrainz.model import MBRecording

PGUuid = postgres.PGUuid
Base = declarative_base(metadata=metadata)
class PlaylistItem(Base):

    __tablename__ = 'scatterbrainz_playlist_items'
    
    playlist_id = Column(Integer, ForeignKey('scatterbrainz_playlists.playlist_id'), nullable=False, primary_key=True)
    track_id = Column(PGUuid, ForeignKey('recording.gid'), nullable=False)
    track = orm.relation(MBRecording)
    position = Column(Integer, nullable=False, primary_key=True)
    
    def __init__(self, track):
        self.track = track

