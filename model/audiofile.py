from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import Column, Integer, String, Unicode, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.databases import postgres

from scatterbrainz.model.meta import metadata
from scatterbrainz.model.musicbrainz import *

from scatterbrainz.controllers import renderer as r

PGUuid = postgres.PGUuid
Base = declarative_base(metadata=metadata)
class AudioFile(Base):

    __tablename__ = 'scatterbrainz_files'
    __table_args__ = (UniqueConstraint('releasembid','recordingmbid'),{})

    id = Column(Integer, primary_key=True)
    
    # Joins
    releasembid = Column(u'releasembid', PGUuid(), ForeignKey('release.gid'), primary_key=False, nullable=False)
    release = orm.relation(MBRelease, backref='tracks')
    recordingmbid = Column(u'recordingmbid', PGUuid(), ForeignKey('recording.gid'), primary_key=False, nullable=False)
    recording = orm.relation(MBRecording, backref='tracks')
    
    # Filesystem props
    filepath = Column(Unicode, nullable=False)
    filesize = Column(Integer, nullable=False)
    filemtime = Column(DateTime, nullable=False)
    
    # MP3 props
    mp3bitrate = Column(Integer, nullable=False)
    mp3samplerate = Column(Integer, nullable=False)
    mp3length = Column(Integer, nullable=False)
    
    # Lyrics
    lyrics = Column(Unicode)
    lastHitLyricWiki = Column(DateTime)
    
    # Meta props
    added = Column(DateTime, nullable=False)

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
    
    def getTrackNum(self):
        if self.id3tracknum:
            return int(self.id3tracknum.split('/')[0])
        else:
            return None
    
    def toPlaylistJSON(self):
        return dict(id = self.id,
                    title = r.title(self),
                    artist = r.artist(self),
                    artistid = r.artistid(self),
                    album = r.album(self),
                    albumid = r.albumid(self),
                    tracknum = r.tracknum(self),
                    filepath = r.filepath(self),
                    bitrate = r.bitrate(self),
                    length = r.length(self))
    
    def toTreeJSON(self):
        json = {
                'attributes': {'id'   : self.__class__.__name__ + '_' + str(self.id),
                               'class': 'browsenode',
                               'rel'  : self.__class__.__name__
                              },
                'data': self.id3title or "&nbsp;" # jstree bug triggers on null or ""
               }
        return json

    def __repr__(self):
        return "<Track%s>" % (self.__dict__)

