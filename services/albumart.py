import re
import urllib
import urllib2
import logging

from datetime import datetime, timedelta

log = logging.getLogger(__name__)

def get_art(Session, album):
    if album.albumArtFilename is not None:
        return album.albumArtFilename
    elif album.lastHitAlbumArtExchange is None \
        or datetime.now() > album.lastHitAlbumArtExchange + timedelta(days=30):
        
        album.lastHitAlbumArtExchange = datetime.now()
        
        if album.artist.name == 'Various Artists':
            q = album.name
        else:
            q = (album.artist.name + ' ' + album.name)
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
                image = thumb.replace('.tn', '').replace('/_','/')
                album.albumArtFilename = _fetchAlbumArt(album.artist.name, album.name, image)
            else:
                raise Exception('Didnt find message for no images, but couldnt locate one')
        Session.begin()
        Session.commit()
        return album.albumArtFilename
    else:
        return None

def _fetchAlbumArt(artist, album, url):
    extension = url.rsplit('.', 1)[1]
    delchars = ''.join(c for c in map(chr, range(256)) if not c.isalnum())
    delchars = delchars.translate(None," ()'&!-+_.")
    filename = (artist + ' - ' + album).encode('utf-8').translate(None, delchars) + '.' + extension
    filepath = 'scatterbrainz/public/art/' + filename
    log.info('[art] Saving ' + url + ' to ' + filepath)
    urllib.urlretrieve(url, filepath)
    return unicode('/art/' + filename)

