from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import Column, Integer, String, Unicode, DateTime, ForeignKey
from sqlalchemy.databases.postgres import PGUuid

from scatterbrainz.model.meta import metadata

from scatterbrainz.controllers import renderer as r

Base = declarative_base(metadata=metadata)
class Track(Base):

    __tablename__ = 'scatterbrainz_tracks'
    
    id = Column(u'stable_id', Unicode, primary_key=True)
    fileid = Column(u'file_id', Integer(), ForeignKey('scatterbrainz_files.id'), primary_key=False)
    mbid = Column(u'track_mbid', PGUuid(), nullable=False)
    albumid = Column(u'release_group_mbid', PGUuid(), ForeignKey('scatterbrainz_albums.release_group_mbid'), nullable=False)
    name = Column(u'track_name', Unicode, nullable=False)
    tracknum = Column(u'track_number', Integer(), nullable=False)
    discnum = Column(u'disc_number', Integer())
    releasename = Column(u'release_name', Unicode, nullable=False)
    artistcredit = Column(u'artist_credit_name', Unicode, nullable=False)
    
    def __init__(self, filepath, filesize, filemtime, mp3bitrate,
                 mp3samplerate, mp3length, release, recording, added):
        self.filepath = filepath
        self.filesize = filesize
        self.filemtime = filemtime
        self.mp3bitrate = mp3bitrate
        self.mp3samplerate = mp3samplerate
        self.mp3length = mp3length
        self.release = release
        self.recording = recording
        self.added = added
    
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

