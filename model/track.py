from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import Column, Integer, String, Unicode, DateTime, ForeignKey
from sqlalchemy.databases import postgres

from scatterbrainz.model.meta import metadata

from scatterbrainz.controllers import renderer as r

PGUuid = postgres.PGUuid
Base = declarative_base(metadata=metadata)
class Track(Base):

    __tablename__ = 'scatterbrainz_tracks'
    
    id = Column(u'stable_id', Unicode, primary_key=True)
    fileid = Column(u'file_id', Integer(), ForeignKey('scatterbrainz_files.id'), primary_key=False)
    mbid = Column(u'track_mbid', PGUuid(), ForeignKey('recording.gid'), nullable=False)
    albumid = Column(u'release_group_mbid', PGUuid(), ForeignKey('scatterbrainz_albums.release_group_mbid'), nullable=False)
    name = Column(u'track_name', Unicode, nullable=False)
    tracknum = Column(u'track_number', Integer(), nullable=False)
    discnum = Column(u'disc_number', Integer())
    releasename = Column(u'release_name', Unicode, nullable=False)
    artistcredit = Column(u'artist_credit_name', Unicode, nullable=False)
    
    def __init__(self, id, fileid, mbid, albumid, name, tracknum, discnum, releasename, artistcredit):
        self.id = id
        self.fileid = fileid
        self.mbid = mbid
        self.albumid = albumid
        self.name = name
        self.tracknum = tracknum
        self.discnum = discnum
        self.releasename = releasename
        self.artistcredit = artistcredit
    
    def toPlaylistJSON(self):
        return dict(id = self.id,
                    title = self.name,
                    artist = self.artistcredit,
                    artistid = '???',
                    album = self.releasename,
                    albumid = self.albumid,
                    tracknum = self.tracknum or '',
                    discnum = self.discnum or '',
                    filepath = r.filepath(self.file),
                    bitrate = r.bitrate(self.file),
                    length = r.length(self.file))
    
    def toTreeJSON(self):
        json = {
                'attributes': {'id'   : self.__class__.__name__ + '_' + str(self.id),
                               'class': 'browsenode',
                               'rel'  : self.__class__.__name__
                              },
                'data': self.name or "&nbsp;" # jstree bug triggers on null or ""
               }
        return json

    def __repr__(self):
        return "<Track%s>" % (self.__dict__)

