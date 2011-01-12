import os
from datetime import datetime

import logging
from mutagen.mp3 import MP3
from mutagen.mp3 import HeaderNotFoundError
from mutagen.easyid3 import EasyID3

from pylons import request, response, session, tmpl_context as c

from scatterbrainz.lib.base import BaseController, render

from scatterbrainz.model.meta import Session
from scatterbrainz.model.audiofile import AudioFile
from scatterbrainz.model.album import Album
from scatterbrainz.model.musicbrainz import *

log = logging.getLogger(__name__)

def _msg(s, msg):
    log.info(msg)
    return s + msg + '<br><br>'

BASE = '/home/dan/dev/pylons/scatterbrainz/scatterbrainz/'
INCOMING = '/media/data/incoming/ds'
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
        initialLoad = True #Session.query(AudioFile).count() == 0
        
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
        release_groups_added = set()
        unknownrelease = set()
        unknownrecording = set()
        alreadyhaverecordingrelease = set()
        alreadyhavereleasegroup = set()
        unicodeproblems = set()
        fuckedmp3s = set()

        for dirname, dirnames, filenames in os.walk(INCOMING, followlinks=True):

            for filename in filenames:
            
                if not os.path.splitext(filename)[-1].lower() == '.mp3':
                    continue
                
                try:
                    filepath = os.path.join(os.path.relpath(dirname, INCOMING), filename).decode('utf-8')
                except UnicodeDecodeError:
                    log.error('unicode problem ' + os.path.join(os.path.relpath(dirname, INCOMING), filename))
                    unicodeproblems.add(os.path.join(os.path.relpath(dirname, INCOMING), filename))
                    continue
                
                if not initialLoad and filepath in filepaths:
                    continue
                
                if not initialLoad:
                    s = _msg(s, 'New file: ' + filepath)
                
                if not commit:
                    continue
                
                # get size, date
                fileabspath = os.path.join(dirname,filename)
                filesize = os.path.getsize(fileabspath)
                filemtime = datetime.fromtimestamp(os.path.getmtime(fileabspath))
                
                # mp3 length, bitrate, etc.
                try:
                    mutagen = MP3(fileabspath)
                except:
                    fuckedmp3s.add(fileabspath)
                    log.error('fucked mp3 ' + fileabspath)
                    continue
                info = mutagen.info
                mp3bitrate = info.bitrate
                mp3samplerate = info.sample_rate
                mp3length = int(round(info.length))
                if info.sketchy:
                    fuckedmp3s.add(fileabspath)
                    log.error('sketchy mp3! ' + fileabspath)
                    continue
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
                    release = Session.query(MBRelease) \
                                     .join(MBReleaseGIDRedirect) \
                                     .filter(MBReleaseGIDRedirect.gid==releasembid) \
                                     .first()
                if release is None:
                    if releasembid not in unknownrelease:
                        log.error('couldnt find release mbid ' + releasembid)
                        unknownrelease.add(releasembid)
                    continue
                
                recording = Session.query(MBRecording).filter(MBRecording.gid==recordingmbid).first()
                if recording is None:
                    recording = Session.query(MBRecording) \
                                       .join(MBRecordingGIDRedirect) \
                                       .filter(MBRecordingGIDRedirect.gid==recordingmbid) \
                                       .first()
                if recording is None:
                    if recordingmbid not in unknownrecording:
                        log.error('couldnt find recording mbid ' + recordingmbid)
                        unknownrecording.add(recordingmbid)
                    continue
                    
                releasegroupmbid = release.releasegroup.gid
                dirs = os.path.join(releasegroupmbid[:2], releasegroupmbid)
                newdir = os.path.join(MUSIC, dirs)
                if releasegroupmbid not in release_groups_added:
                    existing = Session.query(Album) \
                                      .filter(Album.mbid==releasegroupmbid) \
                                      .first()
                    if existing != None:
                        if releasegroupmbid not in alreadyhavereleasegroup:
                            log.info('already have release group ' + existing.artistcredit + ' ' + existing.name + ' ' + existing.mbid)
                            alreadyhavereleasegroup.add(releasegroupmbid)
                        continue
                    else:
                        os.makedirs(newdir)
                        release_groups_added.add(releasegroupmbid)
                
                existing = Session.query(AudioFile) \
                                  .filter(AudioFile.recordingmbid==recording.gid) \
                                  .filter(AudioFile.releasembid==release.gid) \
                                  .first()
                if existing:
                    if (recording.gid + '-' + release.gid) not in alreadyhaverecordingrelease:
                        log.error('already existing recording/release combo for file ' + filepath)
                        alreadyhaverecordingrelease.add(recording.gid + '-' + release.gid)
                    continue

                # check for existing release group, make new release group directory if necessary               
                # link file into new directory
                newfilename = release.gid + '-' + recording.gid + '.mp3'
                ln = os.path.join(newdir, newfilename)
                os.link(fileabspath, ln)
                lnrelpath = os.path.join(dirs, newfilename)

                track = AudioFile(filepath=lnrelpath,
                              filesize=filesize,
                              filemtime=filemtime,
                              mp3bitrate=mp3bitrate,
                              mp3samplerate=mp3samplerate,
                              mp3length=mp3length,
                              recording=recording,
                              release=release,
                              added=now,
                )
                Session.add(track)
                added = added + 1
 
        if commit:
            s = _msg(s, 'Building model for new tracks took ' + str(datetime.now() - then))
            then = datetime.now()
            
            Session.commit()
            s = _msg(s, """Committed %(added)d new tracks, skipped %(skipped)d""" \
                   % {'added':added-skippedNoMBID, 'skipped':skippedNoMBID} + ', took ' + str(datetime.now() - then))
            log.error("unknownrelease: " + unknownrelease.__str__())
            log.error("unknownrecording: " + unknownrecording.__str__())
            log.error("alreadyhaverecordingrelease: " + alreadyhaverecordingrelease.__str__())
            log.error("alreadyhavereleasegroup: " + alreadyhavereleasegroup.__str__())
            log.error("unicodeproblems: " + unicodeproblems.__str__())
            log.error("fuckedmp3s: " + fuckedmp3s.__str__())
        else:
            s = _msg(s, 'Saw ' + str(added) + ' new tracks, took ' + str(datetime.now() - then))
        return s

