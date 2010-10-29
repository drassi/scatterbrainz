import os
from datetime import datetime

import logging
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3

from pylons import request, response, session, tmpl_context as c

from scatterbrainz.lib.base import BaseController, render

from scatterbrainz.model.meta import Session
from scatterbrainz.model.audiofile import AudioFile
#from scatterbrainz.model.artist import Artist
#from scatterbrainz.model.album import Album
from scatterbrainz.model.musicbrainz import *

log = logging.getLogger(__name__)

def _msg(s, msg):
    log.info(msg)
    return s + msg + '<br><br>'

BASE = '/home/dan/dev/pylons/scatterbrainz/scatterbrainz/'
MUSIC = BASE + 'public/music'
VIEW = BASE + '/views/views.sql'
RECORDING_MBID_KEY = 'UFID:http://musicbrainz.org'
RELEASE_MBID_KEY = 'TXXX:MusicBrainz Album Id'

class LoadController(BaseController):

    def view(self):
        sql = open(VIEW).read()
        then = datetime.now()
        Session.execute(sql)
        return 'OK!  took ' + str(datetime.now() - then)
    
    def load(self):
    
        commit = 'commit' in request.params and request.params['commit'] == 'true'
    
        s = ''
        
        if commit:
            Session.begin()
        
        now = datetime.now()
        initialLoad = Session.query(AudioFile).count() == 0
        
        if initialLoad:
            s = _msg(s, 'Initial track loading!')
        else:
            s = _msg(s, 'Updating tracks!')
            then = now
            
            missing = 0
            changed = 0
            for track in Session.query(AudioFile):
                path = os.path.join(MUSIC, track.filepath)
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
            
            filepaths = set(map(lambda t: t.filepath, Session.query(AudioFile)))
            s = _msg(s, 'Querying for all filepaths took ' + str(datetime.now() - then))
        
        then = datetime.now()
        
        added = 0
        skippedNoMBID = 0
        
        for dirname, dirnames, filenames in os.walk(MUSIC, followlinks=True):

            for filename in filenames:
            
                filepath = os.path.join(os.path.relpath(dirname, MUSIC), filename).decode('utf-8')
                
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
                mutagen = MP3(fileabspath)
                info = mutagen.info
                mp3bitrate = info.bitrate
                mp3samplerate = info.sample_rate
                mp3length = int(round(info.length))
                if info.sketchy:
                    raise Exception('sketchy mp3! ' + filename)
                
                # brainz!!
                if RECORDING_MBID_KEY not in mutagen:
                    skippedNoMBID = skippedNoMBID + 1
                    continue
                recordingmbid = mutagen[RECORDING_MBID_KEY].data
                if not recordingmbid:
                    skippedNoMBID = skippedNoMBID + 1
                    continue
                
                if RELEASE_MBID_KEY not in mutagen:
                    skippedNoMBID = skippedNoMBID + 1
                    continue
                releasembid = mutagen[RELEASE_MBID_KEY].text[0]
                if not releasembid or len(mutagen[RELEASE_MBID_KEY].text) > 1:
                    skippedNoMBID = skippedNoMBID + 1
                    continue
                    
                release = Session.query(MBRelease).filter(MBRelease.gid==releasembid).first()
                if release is None:
                    release = Session.query(MBRelease).filter(MBReleaseGIDRedirect.gid==releasembid).first()
                if release is None:
                    raise Exception('couldnt find release mbid ' + releasembid)
                
                recording = Session.query(MBRecording).filter(MBRecording.gid==recordingmbid).first()
                if recording is None:
                    recording = Session.query(MBRecording).filter(MBRecordingGIDRedirect.gid==recordingmbid).first()
                if recording is None:
                    raise Exception('couldnt find recording mbid ' + recordingmbid)

                track = AudioFile(filepath=filepath,
                              filesize=filesize,
                              filemtime=filemtime,
                              mp3bitrate=mp3bitrate,
                              mp3samplerate=mp3samplerate,
                              mp3length=mp3length,
                              recording=recording,
                              release=release,
                              added=now,
                )
                Session.save(track)
        
        if commit:
            s = _msg(s, 'Building model for new tracks took ' + str(datetime.now() - then))
            then = datetime.now()
            
            Session.commit()
            s = _msg(s, """Committed %(added)d new tracks, skipped %(skipped)d""" \
                   % {'added':added-skippedNoMBID, 'skipped':skippedNoMBID} + ', took ' + str(datetime.now() - then))
        else:
            s = _msg(s, 'Saw ' + str(added) + ' new tracks, took ' + str(datetime.now() - then))
        return s

