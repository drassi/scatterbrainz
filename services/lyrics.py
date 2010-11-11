import re
import time
import urllib
import logging
import simplejson
import unicodedata
from datetime import datetime, timedelta

from scatterbrainz.model.lyrics import Lyrics
from scatterbrainz.model.lyricsattempt import LyricsAttempt

log = logging.getLogger(__name__)

def get_lyrics(Session, track):
    recording_mbid = track.mbid
    lyrics = Session.query(Lyrics).filter_by(mbid=recording_mbid).first()
    if lyrics:
        return lyrics.lyrics
    else:
        now = datetime.now()
        foundlyrics = None
        lyricsAttempt = Session.query(LyricsAttempt).filter_by(mbid=recording_mbid).first()
        if lyricsAttempt is None or now > lyricsAttempt.tried + timedelta(days=30):
        
            Session.begin()
            try:
                title = unicodedata.normalize('NFKD', track.name).encode('ascii', 'ignore')
                artist = unicodedata.normalize('NFKD', track.artistcredit).encode('ascii', 'ignore')
                params = {
                    'artist' : artist,
                    'song'   : title,
                    'fmt'    : 'json',
                }
                
                wikia = 'http://lyrics.wikia.com/'
                url = wikia + ('api.php?%s' % urllib.urlencode(params))
                
                log.info('[lyric] Hitting ' + url)
                html = urllib.urlopen(url).read()
                
                if not "'lyrics':'Not found'" in html:
                    search = re.search("'url':'(?P<url>.*?)'",html)
                    lyricurl = urllib.unquote(search.group('url'))
                    assert(lyricurl.startswith(wikia))
                    page = urllib.quote(lyricurl.replace(wikia,''))
                    lyricurl = 'http://lyrics.wikia.com/index.php?title='+page+'&action=edit'
                    log.info('[lyric] Hitting ' + lyricurl)
                    lyrichtml = urllib.urlopen(lyricurl).read()
                    lyricREstr = "&lt;lyrics&gt;(?P<lyrics>.*)&lt;/lyrics&gt;"
                    lyricRE = re.search(lyricREstr, lyrichtml, re.S)
                    if lyricRE:
                        lyrics = lyricRE.group('lyrics').strip('\n')
                        if '{{gracenote_takedown}}' in lyrics:
                            historyurl = 'http://lyrics.wikia.com/index.php?title='+page+'&action=history'
                            log.info('[lyric] Found gracenote takedown, hitting ' + historyurl)
                            historyhtml = urllib.urlopen(historyurl).read()
                            oldidRE = re.search(".*GracenoteBot.*?/index\.php\?title=.*?&amp;oldid=(?P<oldid>\d+)", historyhtml, re.S)
                            if oldidRE:
                                oldid = oldidRE.group('oldid')
                                lyricurl = lyricurl + '&oldid=' + oldid
                                log.info('[lyric] found pre-takedown lyrics! hitting ' + lyricurl)
                                oldlyrichtml = urllib.urlopen(lyricurl).read()
                                lyricRE = re.search(lyricREstr, oldlyrichtml, re.S)
                                if lyricRE:
                                    lyrics = lyricRE.group('lyrics').strip('\n')
                                    if '{{gracenote_takedown}}' in lyrics:
                                        raise Exception('[lyric] Still found takedown lyrics!')
                                    elif '{{Instrumental}}' in lyrics:
                                        foundlyrics = u'(Instrumental)'
                                    else:
                                        foundlyrics = lyrics.replace('\n','<br />').decode('utf-8')
                                else:
                                    log.info('[lyric] failed lyrics!')
                                    raise Exception('failed lyrics 1!')
                            else:
                                raise Exception('no pre-takedown lyrics found :(')
                        elif '{{Instrumental}}' in lyrics:
                            foundlyrics = u'(Instrumental)'
                        else:
                            foundlyrics = lyrics.replace('\n','<br />').decode('utf-8')
                    else:
                        log.info('[lyric] failed lyrics!')
                        raise Exception('failed lyrics 2!')
                else:
                    log.info('[lyric] No results found')
            
                if foundlyrics:
                    Session.add(Lyrics(recording_mbid, foundlyrics, unicode(lyricurl), now))
                    if lyricsAttempt:
                        Session.delete(lyricsAttempt)
                else:
                    if lyricsAttempt:
                        lyricsAttempt.tried = now
                        lyricsAttempt.error = None
                        Session.update(lyricsAttempt)
                    else:
                        Session.add(LyricsAttempt(recording_mbid, now))
            except Exception, e:
                if lyricsAttempt:
                    lyricsAttempt.tried = now
                    lyricsAttempt.error = e.__repr__()
                    Session.update(lyricsAttempt)
                else:
                    Session.add(LyricsAttempt(recording_mbid, now, e.__repr__()))
            Session.commit()
        return foundlyrics

