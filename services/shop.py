import re
import urllib
import urllib2
import difflib
import logging
import hashlib
import bencode
import tempfile
import xmlrpclib
import lxml.html as lxml
from operator import itemgetter
from multiprocessing import Lock
from difflib import SequenceMatcher

from scatterbrainz.config.config import Config

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
def download(Session, mbid):
    with shoplock:
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
        results = Session.query(MBTrack, MBArtistName, MBTrackName, MBRelease) \
                         .join(MBTrackList, MBMedium, MBRelease, MBReleaseGroup) \
                         .join(MBTrackName).join(MBTrack.artistcredit, MBArtistCredit.name) \
                         .filter(MBReleaseGroup.gid==mbid) \
                         .all()
        releases = {}
        for (track, artistname, trackname, release) in results:
            data = {'id' : track.id, 'num' : track.position, 'artist' : artistname.name, 'name' : trackname.name}
            mbid = release.gid
            if mbid in releases:
                releases[mbid].append(data)
            else:
                releases[mbid] = [data]
        for releaseid in releases.keys():
            release = releases[releaseid]
            release.sort(key=itemgetter('num'))
        log.info('[shop] release group ' + mbid + ' has ' + str(len(releases)) + ' releases to check against')
        
        # Try to match any of the releases with the first few results
        torrent_table = page.cssselect('table#torrent_table')[0]
        groups = torrent_table.cssselect('tr.group')
        numresults = len(groups)
        for torrent in groups[:3]:
            torrenturl = shopbaseurl + '/' + torrent.cssselect('a[title="View Torrent"]')[0].attrib['href']
            log.info('[shop] hitting ' + torrenturl)
            thandle = opener.open(torrenturl)
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
                    raise Exception('Torrent ' + torrentid + ' has !=5 TD tags at ' + torrenturl)
                numseeders = int(download.cssselect('td')[3].text.replace(',', ''))
                if numseeders < 1:
                    continue
                filestr = ttable.cssselect('div#files_' + torrentid)[0].cssselect('tr')[1:]
                filenames = []
                for tr in filestr:
                    filename = tr.cssselect('td')[0].text
                    if filename.lower().endswith('.mp3'):
                        filenames.append(filename)
                downloads.append({'seeders' : numseeders, 'torrentid' : torrentid, 'url' : downloadurl, 'filenames' : filenames})
            if not downloads:
                log.info('[shop] no seeded files of correct type found at torrent ' + torrentid)

            # See if any of the downloads nicely match any of the releases, trying best seeded first
            downloads.sort(key=itemgetter('seeders'), reverse=True)
            for download in downloads:
                releasescores = []
                filenames = []
                for filename in download['filenames']:
                    filenames.append(filename.lower()[:-4])
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
                            dname = filenames[i]
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
                    releaseid = releasescores[0]['releaseid']
                    torrenturl = download['url']
                    torrentdata = opener.open(torrenturl).read()
                    torrentdecode = bencode.bdecode(torrentdata)
                    infohash = hashlib.sha1(bencode.bencode(torrentdecode['info'])).hexdigest().upper()
                    with tempfile.NamedTemporaryFile(delete=False) as torrentfile:
                        torrentpath = torrentfile.name
                        torrentfile.write(torrentdata)
                    rtorrent = xmlrpclib.ServerProxy("http://localhost/RPC2")‎
                    rtorrent.load_start(torrentpath, "execute=rm," + torrentpath)
                    log.info('[shop] downloaded ' + torrenturl + ' has ' + str(download['seeders']) +
                             ' seeders, infohash=' + infohash + ', match to album ' + releaseid)
                    return infohash
    log.info('[shop] no matches, sorry :(')
    return None

def getPercentDone(infohash):
    rtorrent = xmlrpclib.ServerProxy("http://localhost/RPC2")
    try:
        done = rtorrent.d.get_bytes_done(infohash)
        total = rtorrent.d.get_size_bytes(infohash)
        return 100 * done / total
    except xmlrpclib.Fault as e:
        if e.faultString == 'Could not find info-hash.':
            return 0
        else:
            raise e

