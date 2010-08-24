import os
from datetime import datetime

import logging
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to

from scatterbrainz.lib.base import BaseController, render

from scatterbrainz.model.meta import Session
from scatterbrainz.model.track import Track
from scatterbrainz.model.rdf import RDFTriple
from scatterbrainz.model.artist import Artist
from scatterbrainz.model.album import Album

log = logging.getLogger(__name__)

def getid3prop(mutagen, prop):
    if prop in mutagen:
        return mutagen[prop][0]
    else:
        return None

BASE = 'scatterbrainz/public/.music/'

class LoadController(BaseController):

    def checkdb(self):
        missing = []
        changed = []
        for track in Session.query(Track):
            path = os.path.join(BASE, track.filepath)
            if os.path.exists(path):
                size = os.path.getsize(path)
                mtime = datetime.fromtimestamp(os.path.getmtime(path))
                if size != track.filesize or mtime != track.filemtime:
                    changed.append(track)
                    print path + ' was changed!'
            else:
                print path + ' doesnt exists!'
                missing.append(track)
        return 'OK!'
    
    def checkfiles(self):
        added = []
        filepaths = set(map(lambda t: t.filepath, Session.query(Track)))
        for dirname, dirnames, filenames in os.walk(BASE):
            for filename in filenames:
                path = os.path.join(os.path.relpath(dirname, BASE), filename).decode('utf-8')
                if path not in filepaths:
                    added.append(path)
                    print path + ' is new file!'
    
    def load(self):
        now = datetime.now()
        numFilesSeen = 0
        numBadFiles = 0
        numSketchy = 0
        albums = {}
        artists = {}
        
        variousArtists = Session.query(Artist).filter_by(mbid='89ad4ac3-39f7-470e-963a-56509c546377').first()
        if variousArtists is None:
            variousArtists = Artist(name='Various Artists',
                                    mbid='89ad4ac3-39f7-470e-963a-56509c546377',
                                    added=now)
            Session.save(variousArtists)
        artists['Various Artists'] = variousArtists

        initialLoad = Session.query(Track).count() == 0
        
        for dirname, dirnames, filenames in os.walk(BASE):
            localAlbums = {}
            for filename in filenames:
                try:

                    # get path and check if we've already seen file
                    filepath = os.path.join(os.path.relpath(dirname, BASE), filename).decode('utf-8')
                    if not initialLoad:
                        if Session.query(Track).filter_by(filepath=filepath).count() != 0:
                            continue
                        else:
                            log.info('Found new track ' + filepath)
                            
                    numFilesSeen = numFilesSeen + 1
                    
                    # get size, date
                    fileabspath = os.path.join(dirname,filename)
                    filesize = os.path.getsize(fileabspath)
                    filemtime = datetime.fromtimestamp(os.path.getmtime(fileabspath))
                     
                    ext = os.path.splitext(filename)[-1]
                    if not ext == '.mp3' and not ext == '.MP3': continue

                    # mp3 length, bitrate, etc.
                    mutagen = MP3(fileabspath, ID3=EasyID3)
                    info = mutagen.info
                    mp3bitrate = info.bitrate
                    mp3samplerate = info.sample_rate
                    mp3length = int(round(info.length))
                    if info.sketchy:
                        mp3['sketchy'] = True
                        numSketchy = numSketchy + 1
                        log.warn('sketchy MP3: ' + filename)

                    # id3
                    # keys: ['album', 'date', 'version', 'composer', 'title'
                    #        'genre', 'tracknumber', 'lyricist', 'artist']

                    id3artist = getid3prop(mutagen, 'artist')
                    id3album = getid3prop(mutagen, 'album')
                    id3title = getid3prop(mutagen, 'title')
                    id3tracknum = getid3prop(mutagen, 'tracknumber')
                    id3date = getid3prop(mutagen, 'date')
                    id3composer = getid3prop(mutagen, 'composer')
                    id3genre = getid3prop(mutagen, 'genre')
                    id3lyricist = getid3prop(mutagen, 'lyricist')
                    
                    # additional musicbrainz related keys: At some point,
                    # should probably switch from easyID3 to ordinary ID3
                    # class to get extra MB relationship data.
                    
                    #mbartistid = getid3prop(mutagen,'musicbrainz_albumartistid')
                    #mbalbumid = getid3prop(mutagen,'musicbrainz_albumid')
                    #mbtrackid = getid3prop(mutagen,'musicbrainz_trackid')

                    if not id3artist:
                        artist = None
                    elif id3artist in artists:
                        artist = artists[id3artist]
                    else:
                        if initialLoad:
                            artistFromDb = None
                        else:
                            artistFromDb = Session.query(Artist).filter_by(name=id3artist).first()
                        if artistFromDb is None:
                            artist = Artist(name=id3artist,
                                             mbid=None,
                                             added=now)
                            Session.save(artist)
                        else:
                            artist = artistFromDb
                        artists[id3artist] = artist
                    
                    if not id3album:
                        album = None
                    elif id3album in localAlbums:
                        album = localAlbums[id3album]
                        if artist != album.artist:
                            album.artist = variousArtists
                    else:
                        album = Album(name=id3album,
                                      artist=artist,
                                      added=now)
                        Session.save(album)
                        albums[id3album] = album
                        localAlbums[id3album] = album
                    
                    track = Track(artist=artist,
                                  album=album,
                                  filepath=filepath,
                                  filesize=filesize,
                                  filemtime=filemtime,
                                  mp3bitrate=mp3bitrate,
                                  mp3samplerate=mp3samplerate,
                                  mp3length=mp3length,
                                  id3artist=id3artist,
                                  id3album=id3album,
                                  id3title=id3title,
                                  id3tracknum=id3tracknum,
                                  id3date=id3date,
                                  id3composer=id3composer,
                                  id3genre=id3genre,
                                  id3lyricist=id3lyricist,
                                  added=now,
                                  mbid=None,
                                  )
                    
                    Session.save(track)
                
                except Exception as e:
                    numBadFiles = numBadFiles + 1
                    log.error('Could not load file "' + filename + '" due to exception: '
                              + e.__class__.__name__ + ': ' + str(e))
        otherNow = datetime.now()

        return """Saw %(numFilesSeen)d tracks, %(numArtists)d artists and %(numAlbums)d albums.
                  %(numBadFiles)d failed, %(numSketchy)d sketchy.  Loaded in %(time)s""" \
               % {'numFilesSeen':numFilesSeen, 'numBadFiles':numBadFiles,
                  'numArtists': len(artists), 'numAlbums': len(albums),
                  'numSketchy' : numSketchy, 'time' : str(otherNow - now)}

