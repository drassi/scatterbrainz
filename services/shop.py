import os
import re
import urllib
import urllib2
import difflib
import logging
import hashlib
import bencode
import tempfile
import xmlrpclib
import simplejson
import lxml.html as lxml
from mutagen.mp3 import MP3
from datetime import datetime
from multiprocessing import Lock
from difflib import SequenceMatcher
from operator import itemgetter, attrgetter

from scatterbrainz.config.config import Config

from scatterbrainz.model import ShopDownload, Album, Artist, Track, AudioFile, artist_albums
from scatterbrainz.model.musicbrainz import *

log = logging.getLogger(__name__)

cookies = urllib2.HTTPCookieProcessor()
opener = urllib2.build_opener(cookies)
agent = "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/534.13 (KHTML, like Gecko) Chrome/9.0.597.84 Safari/534.13"
opener.addheaders = [('User-agent', agent)]
shoplock = Lock()
shopbaseurl = Config.SHOP_URL
loginurl = shopbaseurl + '/login.php'
searchurl = shopbaseurl + '/torrents.php'
maybeloggedin = False
rpcurl = "http://localhost/RPC2"
loadlock = Lock()

def login():
    authdata = urllib.urlencode({
        'username'   : Config.SHOP_USER,
        'password'   : Config.SHOP_PASSWORD,
        'keeplogged' : 1,
        'login'      : 'Login'
    })
    response = opener.open(loginurl, authdata)
    if response.geturl() == loginurl or loginurl in response.read():
        raise Exception('couldnt login!')
    log.info('[shop] login success!')
    maybeloggedin = True

"""
Search the shop for the given album.  Return torrent info hash, or None if album wasn't found
"""
def download(Session, mbid, owner_id):
    with shoplock:
        # TODO check for shopdownload and shopdownloadattempt
        log.info('[shop] searching for ' + mbid)
        if not maybeloggedin:
            login()
        (album, albumname, artistname) = Session.query(MBReleaseGroup, MBReleaseName, MBArtistName) \
                                                .join(MBReleaseName) \
                                                .join(MBReleaseGroup.artistcredit, MBArtistCredit.name) \
                                                .filter(MBReleaseGroup.gid==mbid) \
                                                .one()
        url = searchurl + '?' + urllib.urlencode({
                                    'artistname' : artistname.name,
                                    'groupname'  : albumname.name,
                                    'action'     : 'advanced',
                                    'format'     : 'MP3',
                                    'order_by'   : 'seeders'
                                })
        log.info('[shop] hitting ' + url)
        handle = opener.open(url)
        page = lxml.parse(handle).getroot()
        html = lxml.tostring(page)
        if loginurl in html:
            log.warn('[shop] login url found in search result, logging in..')
            login()
            handle = opener.open(url)
            page = lxml.parse(handle).getroot()
            html = lxml.tostring(page)
            if loginurl in html:
                log.error('[shop] couldnt login!')
                raise Exception('couldnt login!')
        if 'Your search did not match anything' in html:
            log.warn('[shop] no results')
            return None

        # Gather up all tracks from all releases
        results = Session.query(MBTrack, MBArtistName, MBTrackName, MBRelease, MBMedium) \
                         .join(MBTrackList, MBMedium, MBRelease, MBReleaseGroup) \
                         .join(MBTrackName).join(MBTrack.artistcredit, MBArtistCredit.name) \
                         .filter(MBReleaseGroup.gid==mbid) \
                         .all()
        releases = {}
        for (track, artistname, trackname, release, medium) in results:
            data = {'id' : track.id, 'num' : track.position, 'disc' : medium.position, 'artist' : artistname.name, 'name' : trackname.name}
            mbid = release.gid
            if mbid in releases:
                releases[mbid].append(data)
            else:
                releases[mbid] = [data]
        for releaseid in releases.keys():
            release = releases[releaseid]
            release.sort(key=itemgetter('disc'))
            release.sort(key=itemgetter('num'))
        log.info('[shop] release group ' + mbid + ' has ' + str(len(releases)) + ' releases to check against')
        
        # Try to match any of the releases with the first few results
        torrent_table = page.cssselect('table#torrent_table')[0]
        groups = torrent_table.cssselect('tr.group')
        numresults = len(groups)
        for torrent in groups[:3]:
            torrentpageurl = shopbaseurl + '/' + torrent.cssselect('a[title="View Torrent"]')[0].attrib['href']
            log.info('[shop] hitting ' + torrentpageurl)
            thandle = opener.open(torrentpageurl)
            tpage = lxml.parse(thandle).getroot()
            
            # Gather up information about all downloads for this torrent
            ttable = tpage.cssselect('table.torrent_table')[0]
            downloads = []
            for download in ttable.cssselect('tr.group_torrent[id]'):
                torrentid = re.sub('^torrent', '', download.attrib['id'])
                torrenttype = download.cssselect('a[onclick]')[0].text.encode('ascii', 'ignore').split('/')[0].strip()
                if torrenttype != 'MP3':
                    continue
                downloadurl = download.cssselect('a[title=Download]')[0].attrib['href']
                if len(download.cssselect('td')) != 5:
                    raise Exception('Torrent ' + torrentid + ' has !=5 TD tags at ' + torrentpageurl)
                numseeders = int(download.cssselect('td')[3].text.replace(',', ''))
                if numseeders < 1:
                    continue
                filestr = ttable.cssselect('div#files_' + torrentid)[0].cssselect('tr')[1:]
                filenames = []
                for tr in filestr:
                    filename = tr.cssselect('td')[0].text
                    if filename.lower().endswith('.mp3'):
                        filenames.append({'original' : filename,
                                          'compare' : filename.split('/')[-1][:-4].lower()})
                downloads.append({'seeders' : numseeders, 'torrentid' : torrentid, 'url' : downloadurl, 'filenames' : filenames})
            if not downloads:
                log.info('[shop] no seeded files of correct type found at torrent ' + torrentid)

            # See if any of the downloads nicely match any of the releases, trying best seeded first
            downloads.sort(key=itemgetter('seeders'), reverse=True)
            for download in downloads:
                releasescores = []
                filenames = download['filenames']
                for releaseid in releases.keys():
                    release = releases[releaseid]
                    if len(filenames) != len(release):
                        minscore = 0
                        avgscore = 0
                    else:
                        numtracks = len(release)
                        minscore = None
                        minscoreidx = None
                        sumscore = 0
                        for i in range(numtracks):
                            rtrack = release[i]
                            rtracknum = '%02d' % rtrack['num']
                            rtartist = rtrack['artist'].lower()
                            rtname = rtrack['name'].lower()
                            dname = filenames[i]['compare']
                            name1 = rtracknum + ' ' + rtname
                            name2 = rtracknum + ' ' + rtartist + ' ' + rtname
                            score1 = SequenceMatcher(None, dname, name1).ratio()
                            score2 = SequenceMatcher(None, dname, name2).ratio()
                            score = max(score1, score2)
                            sumscore = sumscore + score
                            if score < minscore or minscore is None:
                                minscore = score
                                minscoreidx = i
                        avgscore = sumscore * 1.0 / numtracks
                        log.info('match avg=' + str(avgscore) + ' min=' + str(minscore) + ' ' + download['torrentid'] + ' -> ' + releaseid)
                    releasescores.append({'releaseid' : releaseid, 'min' : minscore, 'avg' : avgscore})
                releasescores = filter(lambda x: x['min'] > 0.6 and x['avg'] > 0.7, releasescores)
                releasescores.sort(key=itemgetter('avg'), reverse=True)
                if releasescores:
                    # Toss torrent over to rtorrent via xml-rpc
                    releaseid = releasescores[0]['releaseid']
                    torrenturl = shopbaseurl + '/' + download['url']
                    torrentdata = opener.open(torrenturl).read()
                    torrentdecode = bencode.bdecode(torrentdata)
                    infohash = hashlib.sha1(bencode.bencode(torrentdecode['info'])).hexdigest().upper()
                    with tempfile.NamedTemporaryFile(delete=False) as torrentfile:
                        torrentpath = torrentfile.name
                        torrentfile.write(torrentdata)
                    rtorrent = xmlrpclib.ServerProxy(rpcurl)
                    rtorrent.load_start(torrentpath, "execute=rm," + torrentpath)
                    log.info('[shop] downloaded ' + torrenturl + ' has ' + str(download['seeders']) +
                             ' seeders, infohash=' + infohash + ', match to album ' + releaseid)
                    file_json = simplejson.dumps(map(itemgetter('original'), filenames))
                    minscore = releasescores[0]['min']
                    avgscore = releasescores[0]['avg']
                    shopdownload = ShopDownload(releaseid, infohash, torrenturl, torrentpageurl, download['torrentid'], download['seeders'], file_json, minscore, avgscore, owner_id)
                    Session.begin()
                    Session.add(shopdownload)
                    Session.commit()
                    return infohash
        # TODO insert/update shopdownloadattempt
        log.info('[shop] no matches, sorry :(')
    return None

"""
Return (isdone, pctdone) of a torrent given its infohash
"""
def getPercentDone(infohash):
    rtorrent = xmlrpclib.ServerProxy(rpcurl)
    try:
        iscomplete = rtorrent.d.get_complete(infohash) == 1
        if iscomplete:
            return (True, 100)
        else:
            pct = rtorrent.d.get_bytes_done(infohash) / rtorrent.d.get_size_bytes(infohash)
            return (False, pct)
    except xmlrpclib.Fault as e:
        if e.faultString == 'Could not find info-hash.':
            return (False, 0)
        else:
            raise e

"""
Import a finished torrent
"""
def loadFinishedTorrent(Session, infohash):
    with loadlock:
        Session.begin()
        shopdownload = Session.query(ShopDownload).filter(ShopDownload.infohash==unicode(infohash)).one()
        if shopdownload.isdone:
            return shopdownload.release_mbid
        promisedfiles = simplejson.loads(shopdownload.file_json)
        rtorrent = xmlrpclib.ServerProxy(rpcurl)
        assert rtorrent.d.get_complete(infohash) == 1
        release_mbid = shopdownload.release_mbid
        mbalbum = Session.query(MBReleaseGroup) \
                         .join(MBRelease) \
                         .filter(MBRelease.gid==release_mbid) \
                         .one()
        mbartists = Session.query(MBArtist, MBArtistName) \
                           .join(MBArtistCreditName, MBArtistCredit, MBReleaseGroup) \
                           .join(MBArtist.name) \
                           .filter(MBReleaseGroup.gid==mbalbum.gid) \
                           .all()
        artists = Session.query(Artist) \
                         .filter(Artist.mbid.in_(map(lambda x: x[0].gid, mbartists))) \
                         .all()
        localartistmbids = map(attrgetter('mbid'), artists)
        # Add Album, Artists and artist-album relationships
        insertmaps = []
        for (artist, name) in mbartists:
            if artist.gid not in localartistmbids:
                a = Artist(name.name, artist.gid)
                artists.append(a)
                Session.add(a)
        albumname = mbalbum.name.name
        artistname = mbalbum.artistcredit.name.name
        albummeta = mbalbum.meta[0]
        album = Album(mbalbum.gid, albumname, artistname, albummeta.year, albummeta.month, albummeta.day, artistname + ' ' + albumname)
        album.artists = artists
        Session.add(album)
        # Build up mapping of promised filename -> (Track)
        results = Session.query(MBTrack, MBMedium, MBRecording, MBTrackName) \
                         .join(MBTrackList, MBMedium, MBRelease) \
                         .join(MBRecording) \
                         .join(MBTrack.name) \
                         .filter(MBRelease.gid==release_mbid) \
                         .all()
        tracks = []
        for (track, medium, recording, name) in results:
            stableid = hashlib.md5(release_mbid + '_' + recording.gid +
                                   '_' + str(track.position) + '_' + str(medium.position)).hexdigest()
            track = Track(stableid, None, recording.gid, mbalbum.gid, name.name, track.position, medium.position, albumname, artistname)
            tracks.append(track)
            Session.add(track)
        tracks.sort(key=attrgetter('discnum'))
        tracks.sort(key=attrgetter('tracknum'))
        assert len(promisedfiles) == len(tracks)
        promisedfilemap = {}
        for i in range(len(tracks)):
            normalizedfilename = filter(str.isalnum, promisedfiles[i].lower().encode())
            assert normalizedfilename not in promisedfilemap
            promisedfilemap[normalizedfilename] = tracks[i]
        # Build up mapping of absolute track filename -> (Track, AudioFile),
        # and link files into their proper library location
        trackfiles = []
        now = datetime.now()
        dirpath = album.mbid[:2] + '/' + album.mbid
        os.mkdir(Config.MUSIC_PATH + dirpath)
        torrentdir = rtorrent.d.get_base_path(infohash)
        for root, dirs, actualfiles in os.walk(torrentdir):
            for f in actualfiles:
                abspath = os.path.join(root, f)
                relpath = os.path.join(os.path.relpath(root, torrentdir), f)
                if relpath.startswith('./'):
                    relpath = relpath[2:]
                normalizedfilename = filter(str.isalnum, relpath.lower())
                assert normalizedfilename in promisedfilemap
                track = promisedfilemap[normalizedfilename]
                filepath = dirpath + '/' + release_mbid + '-' + track.mbid + '.mp3'
                os.link(abspath, Config.MUSIC_PATH + filepath)
                filesize = os.path.getsize(abspath)
                filemtime = datetime.fromtimestamp(os.path.getmtime(abspath))
                mutagen = MP3(abspath)
                info = mutagen.info
                mp3bitrate = info.bitrate
                mp3samplerate = info.sample_rate
                mp3length = int(round(info.length))
                audiofile = AudioFile(release_mbid, track.mbid, filepath, filesize, filemtime, mp3bitrate,
                                      mp3samplerate, mp3length, now)
                track.file = audiofile
                trackfiles.append({'track' : track, 'file' : audiofile, 'path' : abspath})
                Session.add(audiofile)
        assert len(trackfiles) == len(tracks) == len(promisedfilemap)
        Session.commit()
        
        return release_mbid

