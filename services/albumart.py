import re
import urllib
import urllib2
import logging
import unicodedata

from datetime import datetime, timedelta
from urllib2 import HTTPError

from scatterbrainz.model.albumart import AlbumArt
from scatterbrainz.model.albumartattempt import AlbumArtAttempt

log = logging.getLogger(__name__)

def get_art(Session, album):
    albumMbid = album.mbid
    albumart = Session.query(AlbumArt).filter_by(mbid=albumMbid).first()
    if albumart:
        return albumart.path
    else:
        now = datetime.now()
        albumArtAttempt = Session.query(AlbumArtAttempt).filter_by(mbid=albumMbid).first()
        albumArtFilename = None
        if albumArtAttempt is None or now > albumArtAttempt.tried + timedelta(days=30):
            
            Session.begin()
            try:
                artistName = album.artistcredit
                albumName = album.name
                albumArtURL = None
                numResults = None
                if artistName == 'Various Artists':
                    q = albumName
                else:
                    q = (artistName + ' ' + albumName)
                q = q.replace("'","")
                q = q.replace("&","")
                q = q.replace("/"," ")
                q = q.replace(")"," ")
                q = q.replace("("," ")
                q = unicodedata.normalize('NFKD', q).encode('ascii', 'ignore')

                site = 'http://www.albumartexchange.com'

                params = {
                    'grid' : '2x7',
                    'sort' : 7,
                    'q'    : q,
                }

                url = site + '/covers.php?%s' % urllib.urlencode(params)
                
                log.info('[art] Hitting ' + url)
                
                req = urllib2.Request(url)
                req.add_header("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_7) AppleWebKit/535.7 (KHTML, like Gecko) Chrome/16.0.912.75 Safari/535.7")
                req.add_header("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
                req.add_header("Accept-Charset", "ISO-8859-1,utf-8;q=0.7,*;q=0.3")
                req.add_header("Accept-Encoding", "gzip,deflate,sdch")
                req.add_header("Accept-Language", "en-US,en;q=0.8")
                req.add_header("Connection", "keep-alive")
                html = urllib2.urlopen(req).read()
                if html.find('id="captcha"') != -1:
                    capurl = 'http://www.albumartexchange.com/captcha.php'
                    log.info('[art] captcha needed, hitting ' + capurl + ' for captcha')
                    cookiemonster = urllib2.HTTPCookieProcessor()
                    opener = urllib2.build_opener(cookiemonster)
                    opener.open(capurl)
                    captcha = cookiemonster.cookiejar._cookies['www.albumartexchange.com']['/']['security_code'].value
                    log.info('[art] found captcha ' + captcha)
                    postdata = urllib.urlencode({'captcha':captcha})
                    html = opener.open(url, postdata).read()
                    if html.find('id="captcha"') == -1:
                        log.info('[art] captcha success')
                    else:
                        log.info('[art] captcha failed')
                        raise Exception('failed captcha')
                nonefound = re.search('There are no images to display\.', html)
                if nonefound:
                    log.info('[art] No results found')
                else:
                    search = re.search('src="(?P<src>/gallery/images/public.*?)"' ,html)
                    if search:
                        thumb = site + urllib.unquote(search.group('src'))
                        albumArtURL = thumb.replace('.tn', '').replace('/_','/')
                        if '<td align=left>One image.</td>' in html:
                            numResults = 1
                        else:
                            numResultsSearch = re.search('<td align=left>(?P<numResults>\d+) images.</td>', html)
                            if not numResultsSearch:
                                numResultsSearch = re.search('<td style="text-align: center; width: 20em;">Images \d+-\d+ of (?P<numResults>\d+).</td>', html)
                            if not numResultsSearch:
                                raise Exception('couldnt find numResults!')
                            numResults = int(numResultsSearch.group('numResults'))
                        albumArtFilename = _fetchAlbumArt(artistName, albumName, albumArtURL)
                    else:
                        raise Exception('Didnt find message for no images, but couldnt locate one')
                if albumArtFilename:
                    Session.add(AlbumArt(albumMbid, albumArtFilename, unicode(albumArtURL), numResults, now))
                    if albumArtAttempt:
                        Session.delete(albumArtAttempt)
                else:
                    if albumArtAttempt:
                        albumArtAttempt.tried = now
                        albumArtAttempt.error = None
                    else:
                        Session.add(AlbumArtAttempt(albumMbid, now))
            except Exception, e:
                if isinstance(e, HTTPError) and e.code==403 and 'BlockScript' in e.read():
                    log.info('[art] got blocked..')
                if albumArtAttempt:
                    albumArtAttempt.tried = now
                    albumArtAttempt.error = e.__repr__()
                else:
                    Session.add(AlbumArtAttempt(albumMbid, now, e.__repr__()))
            Session.commit()
        return albumArtFilename
        

def _fetchAlbumArt(artist, album, url):
    extension = url.rsplit('.', 1)[1]
    delchars = ''.join(c for c in map(chr, range(256)) if not c.isalnum())
    delchars = delchars.translate(None," ()'&!-+_.")
    filename = (artist + ' - ' + album).encode('utf-8').translate(None, delchars) + '.' + extension
    filepath = '/media/data/albumart/' + filename
    log.info('[art] Saving ' + url + ' to ' + filepath)
    urllib.urlretrieve(url, filepath)
    return unicode('/art/' + filename)

