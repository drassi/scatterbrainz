# -*- coding: utf-8 -*-

import os
import re
import time
import urllib
import string
import logging
import random as rand
import simplejson
import htmlentitydefs
from operator import itemgetter, attrgetter

from httplib import BadStatusLine
from socket import timeout as SocketTimeout

from datetime import datetime, timedelta

from sqlalchemy import exists, desc
from sqlalchemy.orm import aliased
from sqlalchemy.sql.functions import random
from sqlalchemy.orm import contains_eager
from sqlalchemy.sql.expression import or_

from pylons import request, response, session, tmpl_context as c

from scatterbrainz.lib.base import BaseController, render

log = logging.getLogger(__name__)

from scatterbrainz.model.meta import Session
from scatterbrainz.model.audiofile import AudioFile
from scatterbrainz.model.album import Album
from scatterbrainz.model.artist import Artist
from scatterbrainz.model.track import Track
from scatterbrainz.model import artist_albums
from scatterbrainz.model.musicbrainz import *
from scatterbrainz.model.auth import User
from scatterbrainz.model import ShopDownload
from scatterbrainz.model import Playlist
from scatterbrainz.model import TrackPlay

from scatterbrainz.config.config import Config
from scatterbrainz.config.bonnaroo import Bonnaroo

from scatterbrainz.services import albumart
from scatterbrainz.services import lyrics as lyricsservice
from scatterbrainz.services import artistbio
from scatterbrainz.services import albumsummary
from scatterbrainz.services import similarartist
from scatterbrainz.services import shop as shopservice

from scatterbrainz.lib import pylast
from scatterbrainz.lib.pylast import WSError

from repoze.what.predicates import has_permission
from repoze.what.plugins.pylonshq import ControllerProtector

@ControllerProtector(has_permission('login'))
class HelloController(BaseController):

    lastfmNetwork = pylast.get_lastfm_network(api_key = Config.LAST_FM_API_KEY,
                                              api_secret = Config.LAST_FM_API_SECRET,
                                              username = Config.LAST_FM_USER,
                                              password_hash = pylast.md5(Config.LAST_FM_PASSWORD))
    scrobbler = lastfmNetwork.get_scrobbler('tst',1.0)
    lastfmNetwork.enable_caching()
    
    def index(self):
        c.username = request.environ['repoze.what.credentials']['repoze.what.userid']
        c.admin = 'admins' in request.environ['repoze.what.credentials']['groups']
        return render('/hello.html')

    def treeBrowseAJAX(self):
        idStr = request.params['id']
        if idStr == 'init':
            return self._allArtistsTreeJSON()
        else:
            [type, mbid] = idStr.split('_',1)
            if type == 'Artist':
                return self._albumsForArtistTreeJSON(mbid)
            elif type == 'Album':
                return self._tracksForAlbumTreeJSON(mbid)
            else:
                raise Exception('bad type '+type)
    
    def playlistBrowseAJAX(self):
        idStr = request.params['id']
        if idStr == 'init':
            return self._allPlaylistsTreeJSON()
        else:
            [type, playlistid] = idStr.split('_',1)
            if type == 'Playlist':
                return self._tracksForPlaylistTreeJSON(playlistid)
            else:
                raise Exception('bad type '+type)
    
    def _allArtistsTreeJSON(self):
        artists = Session.query(Artist).join(artist_albums).all()
        return self._dumpFlatJSON(artists, self._compareArtists)
    
    def _allPlaylistsTreeJSON(self):
        playlists = Session.query(Playlist).order_by(Playlist.name).all()
        return self._dumpFlatJSON(playlists, None)
    
    def _albumsForArtistTreeJSON(self, mbid):
        albums = Session.query(Artist).filter_by(mbid=mbid).one().albums
        albums.sort(self._compareAlbums)
        return self._dumpFlatJSON(albums, None)
    
    def _compareAlbums(self, a, b):
        ar = a.getReleaseDate()
        br = b.getReleaseDate()
        if ar is None and br is None:
            return 0
        elif ar is None and br is not None:
            return 1
        elif ar is not None and br is None:
            return -1
        else:
            return cmp(ar,br)
    
    def _tracksForAlbumTreeJSON(self, mbid):
        tracks = Session.query(Album).filter_by(mbid=mbid).one().tracks
        tracks.sort(self._compareTracks)
        return self._dumpFlatJSON(tracks, None)
    
    def _tracksForPlaylistTreeJSON(self, id):
        tracks = self._getTracksForPlaylist(id)
        return self._dumpFlatJSON(tracks, None)

    def _compareTracks(self, a, b):
        abonus = '(bonus' in a.releasename.lower()
        bbonus = '(bonus' in b.releasename.lower()
        if abonus != bbonus:
            return cmp(abonus, bbonus)
        elif a.releasename != b.releasename:
            return cmp(a.releasename, b.releasename)
        elif a.discnum != b.discnum:
            return cmp(a.discnum, b.discnum)
        elif a.tracknum != b.tracknum:
            return cmp(a.tracknum, b.tracknum)
        else:
            return cmp(a.name, b.name)

    def _dumpFlatJSON(self, results, sortfun=cmp):
        json = map(lambda x: x.toTreeJSON(), results)
        if sortfun:
            json.sort(sortfun)
        return simplejson.dumps(json)
    
    def getTracksAJAX(self):
        idStr = request.params['id']
        [type, id] = idStr.split('_',1)
        if type == 'Track':
            return self._trackPlaylistJSON(id)
        elif type == 'Artist':
            return self._tracksForArtistPlaylistJSON(id)
        elif type == 'Album':
            return self._tracksForAlbumPlaylistJSON(id)
        elif type == 'Playlist':
            return self._tracksForPlaylistJSON(id)
        else:
            raise Exception('bad type '+type)
    
    def randomTrackAJAX(self):
        track = Session.query(Track).order_by(random())[0]
        return simplejson.dumps([track.toPlaylistJSON()])
    
    def randomAlbumAJAX(self):
        album = Session.query(Album).order_by(random())[0]
        tracks = Session.query(Track) \
                        .filter_by(albumid=album.mbid)
        json = map(lambda x: x.toPlaylistJSON(), tracks)
        return simplejson.dumps(json)

    def randomRooTrackAJAX(self):
        track = Session.query(Track) \
                       .join(Album, Album.artists) \
                       .filter(Artist.mbid.in_(Bonnaroo.artist_mbids)) \
                       .order_by(random()) \
                       .first()
        return simplejson.dumps([track.toPlaylistJSON()])
    
    def randomRooAlbumAJAX(self):
        album = Session.query(Album) \
                       .join(Album.artists) \
                       .filter(Artist.mbid.in_(Bonnaroo.artist_mbids)) \
                       .order_by(random()) \
                       .first()
        tracks = Session.query(Track) \
                        .filter_by(albumid=album.mbid)
        json = map(lambda x: x.toPlaylistJSON(), tracks)
        return simplejson.dumps(json)
    
    def similarTrackAJAX(self):
        trackid = request.params['id'].split('_')[1]
        artists = Session.query(MBArtist).join(MBArtistCreditName, MBArtistCredit, MBRecording, AudioFile, AudioFile.track).filter(Track.id==trackid).all()
        similarMbids = set([])
        try:
            for artist in artists:
                similarMbids.update(similarartist.get_similar_artists(Session, self.lastfmNetwork, artist))
        except (BadStatusLine, SocketTimeout) as e:
            log.error('[lastfm] down? ' + e.__repr__())
            return ''
        artistMbidsWithAlbums = Session.query(Artist.mbid) \
                                       .join(artist_albums) \
                                       .filter(Artist.mbid.in_(similarMbids)) \
                                       .distinct() \
                                       .subquery()
        randomSimilarArtist = Session.query(Artist) \
                                     .filter(Artist.mbid.in_(artistMbidsWithAlbums)) \
                                     .order_by(random()) \
                                     .first()
        randomAlbum = rand.choice(randomSimilarArtist.albums)
        randomTrack = rand.choice(randomAlbum.tracks)
        return simplejson.dumps([randomTrack.toPlaylistJSON()])
    
    def _trackPlaylistJSON(self, stableid):
        tracks = [Session.query(Track).filter_by(id=stableid).one()]
        return self._playlistJSON(tracks)
    
    def _tracksForAlbumPlaylistJSON(self, mbid):
        tracks = Session.query(Album).filter_by(mbid=mbid).one().tracks
        tracks.sort(self._compareTracks)
        return self._playlistJSON(tracks)
    
    def _tracksForArtistPlaylistJSON(self, mbid):
        albums = Session.query(Artist).filter_by(mbid=mbid).one().albums
        albums.sort(lambda a,b: cmp(a.getReleaseDate(), b.getReleaseDate()))
        tracks = []
        for album in albums:
            albumtracks = album.tracks
            albumtracks.sort(self._compareTracks)
            tracks.extend(albumtracks)
        return self._playlistJSON(tracks)

    def _getTracksForPlaylist(self, id):
        playlist = Session.query(Playlist).filter(Playlist.playlist_id==id).one()
        recordings = playlist.tracks
        recording_mbids = map(lambda x: x.gid, recordings)
        tracks = Session.query(Track).filter(Track.mbid.in_(recording_mbids)).all()
        tracks.sort(lambda a,b: cmp(recording_mbids.index(a.mbid), recording_mbids.index(b.mbid)))
        filtertracks = [tracks[0]]
        for track in tracks[1:]:
            if track.mbid != filtertracks[-1].mbid:
                filtertracks.append(track)
        return filtertracks
    
    def _tracksForPlaylistJSON(self, id):
        tracks = self._getTracksForPlaylist(id)
        return self._playlistJSON(tracks)

    def _playlistJSON(self, tracks):
        json = map(lambda x: x.toPlaylistJSON(), tracks)
        return simplejson.dumps(json)
    
    ARTIST_SEARCH = "to_tsvector('mb_simple', unaccent(artist_name)) " + \
                 "@@ to_tsquery('mb_simple', :search)"
    
    ALBUM_TRACK_SEARCH = "to_tsvector('mb_simple', unaccent(search)) " + \
                      "@@ to_tsquery('mb_simple', :search)"
    
    def searchAJAX(self):
        search = request.params['search']
        maxResults = 100
        tsquery = ' & '.join(search.split())
        artists = Session.query(Artist) \
                         .filter(self.ARTIST_SEARCH) \
                         .params(search=tsquery) \
                         [0:maxResults]
        albums = Session.query(Album) \
                        .filter(self.ALBUM_TRACK_SEARCH) \
                        .params(search=tsquery) \
                        [0:maxResults]
        tracks = Session.query(Track) \
                        .filter(self.ALBUM_TRACK_SEARCH) \
                        .params(search=tsquery) \
                        [0:maxResults]
        if len(artists) == maxResults or len(tracks) == maxResults or len(albums) == maxResults:
            truncated = True
        else:
            truncated = False
        artistIdToJSON = {}
        albumsIdToJSON = {}
        for artist in artists:
            if artist.mbid not in artistIdToJSON:
                artistJSON = artist.toTreeJSON()
                artistIdToJSON[artist.mbid] = artistJSON
        for album in albums:
            for artist in album.artists:
                if artist.mbid not in artistIdToJSON:
                    artistJSON = artist.toTreeJSON(children=[])
                    artistIdToJSON[artist.mbid] = artistJSON
                    albumJSON = album.toTreeJSON()
                    artistJSON['children'].append(albumJSON)
                    albumsIdToJSON[album.mbid] = albumJSON
                elif 'children' in artistIdToJSON[artist.mbid]:
                    albumJSON = album.toTreeJSON()
                    artistIdToJSON[artist.mbid]['children'].append(albumJSON)
                    albumsIdToJSON[album.mbid] = albumJSON
                else:
                    continue
        for track in tracks:
            for artist in track.album.artists:
                if artist.mbid not in artistIdToJSON:
                    # artist not yet in search results, add artist, album, track
                    artistJSON = artist.toTreeJSON(children=[])
                    artistIdToJSON[artist.mbid] = artistJSON
                    albumJSON = track.album.toTreeJSON(children=[])
                    albumsIdToJSON[track.album.mbid] = albumJSON
                    artistJSON['children'].append(albumJSON)
                    albumJSON['children'].append(track.toTreeJSON())
                else:
                    if 'children' in artistIdToJSON[artist.mbid]:
                        if track.album.mbid not in albumsIdToJSON:
                            # album not yet in search results, add album, track
                            albumJSON = track.album.toTreeJSON(children=[])
                            albumsIdToJSON[track.album.mbid] = albumJSON
                            artistIdToJSON[artist.mbid]['children'].append(albumJSON)
                            albumJSON['children'].append(track.toTreeJSON())
                        else:
                            if 'children' in albumsIdToJSON[track.album.mbid]:
                                # other tracks on this album in search results
                                albumsIdToJSON[track.album.mbid]['children'].append(track.toTreeJSON())
                            else:
                                # album itself matched search results, don't add child tracks
                                continue
                    else:
                        # artist itself matched search results, don't add child tracks
                        continue
        json = artistIdToJSON.values()
        json.sort(self._compareArtists)
        return simplejson.dumps(json)

    def _compareArtists(self, a, b):
        if a['data'] == 'Various Artists':
            return -1
        elif b['data'] == 'Various Artists':
            return 1
        else:
            return cmp(self._removeThe(a['data'].lower()), self._removeThe(b['data'].lower()))
    
    def _removeThe(self, s):
        if s.startswith('the '):
            return s[4:]
        else:
            return s
    
    def debug(self):
        raise Exception
    
    """def clearAlbumArt(self):
        id = request.params['id']
        Session.begin()
        album = Session.query(Album).filter_by(id=id).one()
        album.albumArtFilename = None
        album.lastHitAlbumArtExchange = None
        Session.commit()
        return 'Cleared album art for ' + album.artist.name + ' - ' + album.name
    
    def setAlbumArt(self):
        id = request.params['id']
        url = request.params['url']
        Session.begin()
        album = Session.query(Album).filter_by(id=id).one()
        album.albumArtFilename = albumart._fetchAlbumArt(album.artist.name, album.name, url)
        Session.commit()
        return 'Set album art for ' + album.artist.name + ' - ' + album.name + ' to ' + url + ', saved to ' + album.albumArtFilename"""

    def getAlbumArtAJAX(self):
        trackid = request.params['trackid'].split('_')[1]
        track = Session.query(Track).filter_by(id=trackid).one()
        albumartfilename = albumart.get_art(Session, track.album)
        if albumartfilename:
            return simplejson.dumps({'albumArtURL' : albumartfilename})
        else:
            return '{}'

    def getLyricsAJAX(self):
        trackid = request.params['trackid'].split('_')[1]
        track = Session.query(Track).filter_by(id=trackid).one()
        ip = request.environ['REMOTE_ADDR']
        user_name = request.environ['repoze.what.credentials']['repoze.what.userid']
        user = Session.query(User).filter(User.user_name==user_name).one()
        Session.begin()
        play = TrackPlay(track.mbid, user, ip)
        Session.add(play)
        Session.commit()
        lyrics = lyricsservice.get_lyrics(Session, track)
        if lyrics:
            return simplejson.dumps({'lyrics' : lyrics})
        else:
            return '{}'
    
    def getArtistImagesAJAX(self):
        if 'trackid' in request.params:
            trackid = request.params['trackid'].split('_')[1]
            artistCreditNames = self._getArtistCreditNames(trackid)
            artistMbid = artistCreditNames[0].artist.gid
        elif 'mbid' in request.params:
            artistMbid = request.params['mbid']
        else:
            raise Exception('must supply trackid or artist mbid')
        lfmartist = self.lastfmNetwork.get_artist(None)
        try:
            try:
                images = lfmartist.get_images_by_mbid(artistMbid, limit=20)
            except WSError, e:
                log.warn('Got last.fm WSError [' + e.details + '] retrying with string name')
                artistName = Session.query(MBArtistName.name).join(MBArtist.name).filter(MBArtist.gid==artistMbid).one()[0]
                images = self.lastfmNetwork.get_artist(artistName).get_images(limit=20)
        except (BadStatusLine, SocketTimeout) as e:
            log.error('[lastfm] down? ' + e.__repr__())
            return '{}'
            
        return simplejson.dumps({
            'images' : map(lambda i:[i.sizes.largesquare, i.sizes.original], images)
        })

    def getAlbumInfoAJAX(self):
        trackid = request.params['trackid'].split('_')[1]
        track = Session.query(Track).filter_by(id=trackid).one()
        json = {}
        albumMbid = track.album.mbid
        # get wikipedia from the release group
        wikipedia = Session.query(MBURL.url) \
                           .join(MBLReleaseGroupURL) \
                           .join(MBLink) \
                           .join(MBLinkType) \
                           .filter(MBLinkType.name=='wikipedia') \
                           .join(MBReleaseGroup) \
                           .filter(MBReleaseGroup.gid==albumMbid) \
                           .all()
        wikipedia = filter(self._filterForEnglishWiki, map(lambda x: x[0], wikipedia))
        if wikipedia:
            wurl = wikipedia[0]
            json['wikipedia'] = wurl
            json['summary'] = albumsummary.get_album_summary(Session, albumMbid, wurl)
        # get amazon from any of the releases
        amazon = Session.query(MBURL) \
                        .join(MBLReleaseURL) \
                        .join(MBLink) \
                        .join(MBLinkType) \
                        .filter(MBLinkType.name=='amazon asin') \
                        .join(MBRelease) \
                        .join(MBReleaseGroup) \
                        .filter(MBReleaseGroup.gid==albumMbid) \
                        .first()
        if amazon:
            json['amazon'] = amazon.url
        json['musicbrainz'] = 'http://musicbrainz.org/release-group/' + albumMbid
        return simplejson.dumps(json)
    
    def getArtistInfoAJAX(self):
        json = {}
        # Get the artist credit for the given artist or track
        if 'trackid' in request.params:
            trackid = request.params['trackid'].split('_')[1]
            artistCreditNames = self._getArtistCreditNames(trackid)
            credit = []
            for artistcredit in artistCreditNames:
                credit.append({
                    'text' : artistcredit.name.name,
                    'mbid' : artistcredit.artist.gid
                })
                if artistcredit.joinphrase:
                    credit.append({
                        'text' : artistcredit.joinphrase
                    })
            artistMbid = artistCreditNames[0].artist.gid
        elif 'mbid' in request.params:
            artistMbid = request.params['mbid']
            artist = Session.query(MBArtist).filter(MBArtist.gid==artistMbid).one()
            credit = [{
                'text' : artist.name.name
            }]
        else:
            raise Exception('need trackid or artist mbid')
        json['credit'] = credit
        # Get artist bio, and url relationships
        urls = Session.query(MBURL.url, MBLinkType.name) \
                      .join(MBLArtistURL) \
                      .join(MBLink) \
                      .join(MBLinkType) \
                      .join(MBArtist) \
                      .filter(MBArtist.gid==artistMbid) \
                      .all()
        urls = self._mapify(urls)
        if 'wikipedia' in urls:
            wurls = filter(self._filterForEnglishWiki, urls['wikipedia'])
            if wurls:
                wurl = wurls[0]
                json['wikipedia'] = wurl
                json['bio'] = artistbio.get_artist_bio(Session, artistMbid,  wurl)
        if 'youtube' in urls:
            json['youtube'] = urls['youtube'][0]
        if 'official homepage' in urls:
            json['official'] = urls['official homepage'][0]
        json['musicbrainz'] = 'http://musicbrainz.org/artist/' + artistMbid
        return simplejson.dumps(json)
    
    def getArtistFromTrackAJAX(self):
        trackid = request.params['trackid'].split('_')[1]
        creditname = self._getArtistCreditNames(trackid)[0]
        json = {
            'mbid' : creditname.artist.gid
        }
        return simplejson.dumps(json)
    
    def _getArtistCreditNames(self, trackmbid):
        return Session.query(MBArtistCreditName) \
                      .join(MBArtistCredit, MBRecording, AudioFile, AudioFile.track) \
                      .filter(Track.id==trackmbid) \
                      .order_by(MBArtistCreditName.position) \
                      .all()
    
    def _filterForEnglishWiki(self, url):
        return url.startswith('http://en.wikipedia.org')
    
    def getSimilarArtistsAJAX(self):
        mbid = request.params['mbid']
        artist = Session.query(MBArtist).filter(MBArtist.gid==mbid).one()
        try:
            similarartistmbids = similarartist.get_similar_artists(Session, self.lastfmNetwork, artist)
        except (BadStatusLine, SocketTimeout) as e:
            log.error('[lastfm] down? ' + e.__repr__())
            return '{}'
        similarartists = Session.query(MBArtist, MBArtistName).join(MBArtist.name).filter(MBArtist.gid.in_(similarartistmbids)).all()
        similarmap = {}
        for artist in similarartists:
            similarmap[artist[0].gid] = {'mbid' : artist[0].gid, 'name' : artist[1].name, 'local' : False}
        localsimilarartists = Session.query(Artist).filter(Artist.mbid.in_(similarartistmbids)).all()
        for artist in localsimilarartists:
            similarmap[artist.mbid]['local'] = True
        similarjson = []
        for mbid in similarartistmbids:
            similarjson.append(similarmap[mbid])
        return simplejson.dumps({'similar' : similarjson})
    
    rmap = {
            'member of band' : {'symmetric' : False,
                                'lphrase'   : 'Member of',
                                'rphrase'   : 'Members'},
            'is person'      : {'symmetric' : False,
                                'lphrase'   : 'Performs as',
                                'rphrase'   : 'Performance name for'},
            'parent'         : {'symmetric' : False,
                                'lphrase'   : 'Children',
                                'rphrase'   : 'Parents'},
            'sibling'        : {'symmetric' : True,
                                'phrase'    : 'Siblings'},
            'married'        : {'symmetric' : True,
                                'phrase'    : 'Married'},
            'collaboration'  : {'symmetric' : False,
                                'lphrase'   : 'Collaborated on',
                                'rphrase'   : 'Collaboration between'},
           }
    rkeyorder = ['member of band', 'is person', 'parent', 'sibling', 'married', 'collaboration']

    def getAlbumsAndRelationshipsForArtistAJAX(self):
        
        mbid = request.params['mbid']
        
        # albums
        albums = Session.query(MBReleaseGroup, MBReleaseName, MBReleaseGroupMeta, MBReleaseGroupType) \
                        .join(MBArtistCredit, MBArtistCreditName, MBArtist) \
                        .outerjoin(MBReleaseGroupMeta) \
                        .outerjoin(MBReleaseGroupType) \
                        .join(MBReleaseName) \
                        .filter(MBArtist.gid==mbid) \
                        .order_by([MBReleaseGroupMeta.year, MBReleaseGroupMeta.month, MBReleaseGroupMeta.day]) \
                        .all()
        albummap = {}
        for (album, name, meta, rgtype) in albums:
            if rgtype:
                t = rgtype.name
            else:
                t = 'Unknown'
            if meta and meta.year:
                year = meta.year
            else:
                year = '?'
            albummap[album.gid] = {'mbid' : album.gid,
                                   'type' : t,
                                   'name' : name.name,
                                   'year' : year,
                                   'local' : False}
        localalbums = Session.query(Album).filter(Album.mbid.in_(albummap.keys())).all()
        for album in localalbums:
            albummap[album.mbid]['local'] = True
        albumjson = []
        for (album, name, meta, rgtype) in albums:
            if albummap[album.gid]['type'] != 'Non-Album Tracks':
                albumjson.append(albummap[album.gid])
        
        # weirdly complicated pivoting, collating & sorting of relationship data
        # should be done much better....
        artist1 = aliased(MBArtist)
        artist2 = aliased(MBArtist)
        relations = Session.query(MBLArtistArtist, artist1, artist2, MBLink, MBLinkType) \
                           .join((artist1, MBLArtistArtist.artist1), (artist2, MBLArtistArtist.artist2)) \
                           .join(MBLink, MBLinkType) \
                           .filter(or_(artist1.gid==mbid, artist2.gid==mbid)) \
                           .all()
        rs = {}
        for (r, artist1, artist2, link, linktype) in relations:
            ltype = linktype.name
            if ltype not in self.rmap:
                continue
            sym = self.rmap[ltype]['symmetric']
            if ltype not in rs:
                if sym:
                    rs[ltype] = []
                else:
                    rs[ltype] = [[],[]]
            if artist1.gid == mbid:
                other = artist2
                if sym:
                    place = rs[ltype]
                else:
                    place = rs[ltype][0]
            elif artist2.gid == mbid:
                other = artist1
                if sym:
                    place = rs[ltype]
                else:
                    place = rs[ltype][1]
            else:
                raise Exception('mbid ' + mbid + ' isnt ' + artist1.gid + ' nor ' + artist2.gid)
            rdata = [{'mbid' : other.gid,
                      'text' : other.name.name}]
            if link.beginyear:
                if link.endyear:
                    yeartext = '(' + str(link.beginyear) + u'–' + str(link.endyear) + ')'
                else:
                    yeartext = '(' + str(link.beginyear) + u'–)'
                rdata.append({'text' : yeartext})
            place.append({'begin' : link.beginyear, 'data'  : rdata})
        
        rsordered = []
        for rkey in self.rkeyorder:
        
            if rkey not in rs:
                continue
            
            rmapentry = self.rmap[rkey]
            if rmapentry['symmetric']:
                phrase = rmapentry['phrase']
                data = []
                for relationship in rs[rkey]:
                    data.append(relationship['data'])
                rsordered.append({'text' : phrase, 'data' : data})
            
            else:
                phrase = rmapentry['lphrase']
                data = []
                for relationship in rs[rkey][0]:
                    data.append(relationship['data'])
                if data:
                    rsordered.append({'text' : phrase, 'data' : data})
                
                phrase = rmapentry['rphrase']
                data = []
                for relationship in rs[rkey][1]:
                    data.append(relationship['data'])
                if data:
                    rsordered.append({'text' : phrase, 'data' : data})
            
        return simplejson.dumps({'albums' : albumjson, 'relationships' : rsordered})

    def _searchShopAJAX(self):
        artist = request.params['artist']
        album = request.params['album']
        mbid = request.params['mbid']
        if not artist and not album and not mbid:
            return simplejson.dumps({'albums':[], 'numlocal':0, 'truncated':False})
        query = Session.query(MBReleaseGroup, MBReleaseName, MBArtistName, MBReleaseGroupMeta, MBReleaseGroupType) \
                       .join(MBReleaseName) \
                       .join(MBReleaseGroup.artistcredit, MBArtistCredit.name) \
                       .outerjoin(MBReleaseGroupMeta) \
                       .outerjoin(MBReleaseGroupType) \
                       .filter(~exists().where(MBReleaseGroup.gid==Album.mbid)) \
                       .filter(~exists().where(MBReleaseGroup.gid==ShopDownload.release_group_mbid))
        limit = 30
        if mbid:
            query = query.filter(MBReleaseGroup.gid==mbid)
        else:
            if album:
                query = query.filter("to_tsvector('mb_simple', release_name.name) " + \
                              "@@ plainto_tsquery('mb_simple', :album)") \
                             .params(album=album)
            if artist:
                query = query.filter("to_tsvector('mb_simple', artist_name.name) " + \
                              "@@ plainto_tsquery('mb_simple', :artist)") \
                             .params(artist=artist)
        results = query.limit(limit).all()
        resultmbids = set()
        for (album, albumname, artistname, rgmeta, rgtype) in results:
            resultmbids.add(album.gid)
        albums = []
        for (album, albumname, artistname, rgmeta, rgtype) in results:
            if rgmeta and rgmeta.year:
                year = rgmeta.year
            else:
                year = '?'
            if rgtype and rgtype.name:
                rtype = rgtype.name
            else:
                rtype = 'Unknown'
            albums.append({
                'mbid'   : album.gid,
                'album'  : albumname.name,
                'artist' : artistname.name,
                'year'   : year,
                'type'   : rtype
            })
        truncated = len(results) == limit
        return simplejson.dumps({'albums':albums, 'truncated':truncated})
    
    def _searchShopAlbumAJAX(self):
        mbid = request.params['mbid']
        (album, albumname, artistname) = Session.query(MBReleaseGroup, MBReleaseName, MBArtistName) \
                                                .join(MBReleaseName) \
                                                .join(MBReleaseGroup.artistcredit, MBArtistCredit.name) \
                                                .filter(MBReleaseGroup.gid==mbid) \
                                                .one()
        user_name = request.environ['repoze.what.credentials']['repoze.what.userid']
        user_id = Session.query(User).filter(User.user_name==user_name).one().user_id
        infohash = shopservice.download(Session, mbid, user_id)
        if infohash:
            return simplejson.dumps({'success' : True})
        else:
            return simplejson.dumps({'success' : False})
    
    def checkDownloadStatusesAJAX(self):
        downloadjson = []
        # Everyone's recently finished downloads
        finished = Session.query(ShopDownload, User) \
                          .join(User) \
                          .filter(ShopDownload.isdone==True) \
                          .filter(ShopDownload.finished > datetime.now() - timedelta(days=7)) \
                          .order_by(desc(ShopDownload.finished)) \
                          .all()
        donejson = []
        for (download, user) in finished:
            (album, albumname, artistname, rgmeta, rgtype) = \
                    Session.query(MBReleaseGroup, MBReleaseName, MBArtistName, MBReleaseGroupMeta, MBReleaseGroupType) \
                           .join(MBReleaseName) \
                           .join(MBReleaseGroup.artistcredit, MBArtistCredit.name) \
                           .outerjoin(MBReleaseGroupMeta) \
                           .outerjoin(MBReleaseGroupType) \
                           .filter(MBReleaseGroup.gid==download.release_group_mbid) \
                           .one()
            if rgmeta and rgmeta.year:
                year = rgmeta.year
            else:
                year = '?'
            if rgtype and rgtype.name:
                rtype = rgtype.name
            else:
                rtype = 'Unknown'
            donejson.append({'mbid'   : album.gid,
                             'album'  : albumname.name,
                             'artist' : artistname.name,
                             'year'   : year,
                             'type'   : rtype,
                             'user'   : user.user_name})
        json = {'downloads' : downloadjson, 'done' : donejson}
        return simplejson.dumps(json)
    
    def clearImport(self):
        mbid = request.params['mbid']
        download = Session.query(ShopDownload).filter(ShopDownload.release_group_mbid==mbid).one()
        shopservice.clearimport(download)
        return 'OK'
    
    def savePlaylistAJAX(self):
        playlistname = request.params['name']
        trackids = simplejson.loads(request.params['trackids'])
        trackids = map(lambda x: x.replace('track_',''), trackids)
        results = Session.query(Track, MBRecording).join(MBRecording).filter(Track.id.in_(trackids)).all()
        results.sort(lambda a,b: cmp(trackids.index(a[0].id), trackids.index(b[0].id)))
        recordings = map(itemgetter(1), results)
        Session.begin()
        user_name = request.environ['repoze.what.credentials']['repoze.what.userid']
        user_id = Session.query(User).filter(User.user_name==user_name).one().user_id
        playlist = Session.query(Playlist) \
                          .filter(Playlist.owner_id==user_id) \
                          .filter(Playlist.name==playlistname) \
                          .first()
        if not trackids:
            if playlist is None:
                return '{}'
            else:
                Session.delete(playlist)
        else:
            if playlist is None:
                playlist = Playlist(user_id, playlistname)
                Session.add(playlist)
            else:
                playlist.modified = datetime.now()
            playlist.tracks = recordings
        Session.commit()
        return '{}'
    
    def _mapify(self, urls):
        m = {}
        for (url, name) in urls:
            if name in m:
                m[name].append(url)
            else:
                m[name] = [url]
        return m

