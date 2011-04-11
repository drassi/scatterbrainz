from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import Column, Integer, String, Unicode, DateTime, ForeignKey
from sqlalchemy.databases import postgres

from scatterbrainz.model.meta import metadata

PGUuid = postgres.PGUuid
Base = declarative_base(metadata=metadata)
class Artist(Base):

    __tablename__ = 'scatterbrainz_artists'

    name = Column(u'artist_name', Unicode(), nullable=False)
    mbid = Column(u'artist_mbid', Unicode(), ForeignKey('artist.gid'), primary_key=True)
    
    def __init__(self, name, mbid):
        self.name = name
        self.mbid = mbid

    def toTreeJSON(self, children=None):
        json = {
                'attributes': {'id'   : self.__class__.__name__ + '_' + str(self.mbid),
                               'class': 'browsenode',
                               'rel'  : self.__class__.__name__
                              },
                'data': self.name or "&nbsp;", # jstree bug triggers on null or ""
                'state' : 'closed'
               }
        if children is not None:
            json['state'] = 'open'
            json['children'] = children
        else:
            json['state'] = 'closed'
        return json

    def __repr__(self):
        return "<Artist%s>" % (self.__dict__)
