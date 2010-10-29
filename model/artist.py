from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import Column, Integer, String, Unicode, DateTime
from sqlalchemy.databases.postgres import PGUuid

from scatterbrainz.model.meta import metadata

Base = declarative_base(metadata=metadata)
class Artist(Base):

    __tablename__ = 'scatterbrainz_artists'

    name = Column(u'artist_name', Unicode(), primary_key=True)
    sortname = Column(u'artist_sort_name', Unicode(), nullable=False)
    mbid = Column(u'artist_mbid', Unicode(), nullable=False)

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
