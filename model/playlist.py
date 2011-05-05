import cgi

from datetime import datetime

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import relation
from sqlalchemy import Column, Integer, String, Unicode, DateTime, Boolean, ForeignKey
from sqlalchemy.databases import postgres
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.ext.associationproxy import AssociationProxy

from scatterbrainz.model.meta import metadata

from scatterbrainz.model import PlaylistItem
from scatterbrainz.model import User

PGUuid = postgres.PGUuid
Base = declarative_base(metadata=metadata)
class Playlist(Base):

    __tablename__ = 'scatterbrainz_playlists'
    
    playlist_id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey('scatterbrainz_user.user_id'), nullable=False)
    name = Column(Unicode, nullable=False)
    created = Column(DateTime, nullable=False)
    modified = Column(DateTime, nullable=False)
    
    playlistitems = relation(PlaylistItem,
                             collection_class=ordering_list('position'),
                             order_by=[PlaylistItem.position],
                             cascade='all, delete-orphan')
    tracks = AssociationProxy("playlistitems", "track")
    
    owner = relation(User)

    def __init__(self, owner_id, name):
        self.owner_id = owner_id
        self.name = name
        self.created = self.modified = datetime.now()

    def toTreeJSON(self):
        json = {
                'attributes': {'id'   : self.__class__.__name__ + '_' + str(self.playlist_id),
                               'class': 'browsenode',
                               'rel'  : self.__class__.__name__,
                               'owner' : self.owner.user_name
                              },
                'data': cgi.escape(self.name),
                'state' : 'closed'
               }
        return json

