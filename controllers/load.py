import os
from datetime import datetime

import logging
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3

from pylons import request, response, session, tmpl_context as c

from scatterbrainz.lib.base import BaseController, render

from scatterbrainz.model.meta import Session
from scatterbrainz.model.track import Track
from scatterbrainz.model.rdf import RDFTriple
from scatterbrainz.model.artist import Artist
from scatterbrainz.model.album import Album

log = logging.getLogger(__name__)

def getid3prop(mutagen, prop):
    if prop in mutagen and len(mutagen[prop]) > 0:
        return mutagen[prop][0]
    else:
        return None

def _msg(s, msg):
    log.info(msg)
    return s + msg + '<br><br>'

BASE = 'scatterbrainz/public/.music/'

class LoadController(BaseController):
    
    def load(self):
    
        commit = 'commit' in request.params and request.params['commit'] == 'true'
    
        s = ''
        
        now = datetime.now()

        albums = {}
        artists = {}
        
        if commit:
            Session.begin()
            variousArtists = Session.query(Artist).filter_by(mbid=u'89ad4ac3-39f7-470e-963a-56509c546377').first()
            if variousArtists is None:
                variousArtists = Artist(name=u'Various Artists',
                                        mbid=u'89ad4ac3-39f7-470e-963a-56509c546377',
                                        added=now)
                Session.save(variousArtists)
                s = _msg(s, 'Committed various artists placeholder')
            artists['Various Artists'] = variousArtists

        initialLoad = Session.query(Track).count() == 0
        
        if initialLoad:
            s = _msg(s, 'Initial track loading!')
        else:
            s = _msg(s, 'Updating tracks!')
            then = now
            
            missing = 0
            changed = 0
            for track in Session.query(Track):
                path = os.path.join(BASE, track.filepath)
                if os.path.exists(path):
                    size = os.path.getsize(path)
                    mtime = datetime.fromtimestamp(os.path.getmtime(path))
                    if size != track.filesize or mtime != track.filemtime:
                        changed = changed + 1
                        s = _msg(s, 'Modified file: ' + path)
                        if commit:
                            raise Exception('not implemented!')
                else:
                    s = _msg(s, 'Deleted file: ' + path)
                    missing = missing + 1
                    if commit:
                        Session.delete(track)
            
            s = _msg(s, 'Found ' + str(missing) + ' missing files and ' + str(changed) + ' modified files, took ' + \
                    str(datetime.now() - then))
            then = datetime.now()
            
            filepaths = set(map(lambda t: t.filepath, Session.query(Track)))
            s = _msg(s, 'Querying for all filepaths took ' + str(datetime.now() - then))
        
        then = datetime.now()
        
        added = 0
        
        for dirname, dirnames, filenames in os.walk(BASE):
            localAlbums = {}
            for filename in filenames:
            
                filepath = os.path.join(os.path.relpath(dirname, BASE), filename).decode('utf-8')
                
                if not os.path.splitext(filename)[-1].lower() == '.mp3':
                    continue
                
                if not initialLoad and filepath in filepaths:
                    continue
                
                added = added + 1
                
                if not initialLoad:
                    s = _msg(s, 'New file: ' + filepath)
                
                if not commit:
                    continue
                
                # get size, date
                fileabspath = os.path.join(dirname,filename)
                filesize = os.path.getsize(fileabspath)
                filemtime = datetime.fromtimestamp(os.path.getmtime(fileabspath))
                
                # mp3 length, bitrate, etc.
                mutagen = MP3(fileabspath, ID3=EasyID3)
                info = mutagen.info
                mp3bitrate = info.bitrate
                mp3samplerate = info.sample_rate
                mp3length = int(round(info.length))
                if info.sketchy:
                    raise Exception('sketchy mp3! ' + filename)

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
                
                mbartistid = getid3prop(mutagen,'musicbrainz_albumartistid')
                mbalbumid = getid3prop(mutagen,'musicbrainz_albumid')
                mbtrackid = getid3prop(mutagen,'musicbrainz_trackid')

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
                                         mbartistid=None,
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
                                  added=now,
                                  mbid=mbalbumid)
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
                              mbid=mbtrackid,
                              )
                Session.save(track)
        
        if commit:
            s = _msg(s, 'Building model for new tracks took ' + str(datetime.now() - then))
            then = datetime.now()
            
            Session.commit()
            s = _msg(s, """Committed %(added)d new tracks, %(numArtists)d new artists, %(numAlbums)d new albums""" \
                   % {'added':added, 'numArtists': len(artists), 'numAlbums': len(albums)} + \
                   ', took ' + str(datetime.now() - then))
        else:
            s = _msg(s, 'Saw ' + str(added) + ' new tracks, took ' + str(datetime.now() - then))
        return s

