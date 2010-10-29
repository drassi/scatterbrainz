from datetime import date

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import Column, Integer, String, Unicode, DateTime, Boolean, ForeignKey
from sqlalchemy.databases.postgres import PGUuid

from scatterbrainz.model.meta import metadata

Base = declarative_base(metadata=metadata)
class Album(Base):

    __tablename__ = 'scatterbrainz_albums'

    mbid = Column(u'release_group_mbid', PGUuid(), primary_key=True)
    name = Column(u'release_group_name', Unicode(), nullable=False)
    year = Column(u'release_group_year', Integer())
    month = Column(u'release_group_month', Integer())
    day = Column(u'release_group_day', Integer())
    search = Column(u'search', Unicode())

    def getReleaseDate(self):
        if self.year is not None:
            return date(self.year, self.month or 1, self.day or 1)
        else:
            return None
    
    def getArtistNames(self):
        artists = self.artists
        if len(artists) < 2:
            return artists[0].name
        else:
            names = map(lambda x: x.name, artists)
            return ', '.join(names[:-1]) + ' & ' + names[-1]

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
        return "<Album%s>" % (self.__dict__)

