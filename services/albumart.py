import re
import urllib
import urllib2
import logging

from datetime import datetime, timedelta

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
        if albumArtAttempt is None or now > albumArtAttempt.tried + timedelta(days=30):
            
            Session.begin()
            try:
                artistName = album.artistcredit
                albumName = album.name
                albumArtFilename = None
                albumArtURL = None
                numResults = None
                if artistName == 'Various Artists':
                    q = albumName
                else:
                    q = (artistName + ' ' + albumName)
                q = q.replace("'","")
                q = q.replace("&","")

                site = 'http://www.albumartexchange.com'

                params = {
                    'grid' : '2x7',
                    'sort' : 7,
                    'q'    : q,
                }

                url = site + '/covers.php?%s' % urllib.urlencode(params)
                
                log.info('[art] Hitting ' + url)
                html = urllib2.urlopen(url).read()
                
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
                        Session.update(albumArtAttempt)
                    else:
                        Session.add(AlbumArtAttempt(albumMbid, now))
            except Exception, e:
                if albumArtAttempt:
                    albumArtAttempt.tried = now
                    albumArtAttempt.error = e.__repr__()
                    Session.update(albumArtAttempt)
                else:
                    Session.add(AlbumArtAttempt(albumMbid, now, e.__repr__()))
            Session.commit()
        return albumArtFilename
        

def _fetchAlbumArt(artist, album, url):
    extension = url.rsplit('.', 1)[1]
    delchars = ''.join(c for c in map(chr, range(256)) if not c.isalnum())
    delchars = delchars.translate(None," ()'&!-+_.")
    filename = (artist + ' - ' + album).encode('utf-8').translate(None, delchars) + '.' + extension
    filepath = 'scatterbrainz/public/art/' + filename
    log.info('[art] Saving ' + url + ' to ' + filepath)
    urllib.urlretrieve(url, filepath)
    return unicode('/art/' + filename)

