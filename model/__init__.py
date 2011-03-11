"""The application's model objects"""
import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.databases import postgres

from scatterbrainz.model import meta

def init_model(engine):
    """Call me before using any of the tables or classes in the model"""
    ## Reflected tables must be defined and mapped here
    #global reflected_table
    #reflected_table = sa.Table("Reflected", meta.metadata, autoload=True,
    #                           autoload_with=engine)
    #orm.mapper(Reflected, reflected_table)
    #
    meta.Session.configure(bind=engine)
    meta.engine = engine

from scatterbrainz.model.audiofile import AudioFile
from scatterbrainz.model.album import Album
from scatterbrainz.model.artist import Artist
from scatterbrainz.model.track import Track
from scatterbrainz.model.invite import Invite
from scatterbrainz.model.auth import User, Group, Permission
from scatterbrainz.model.musicbrainz import *
from scatterbrainz.model.albumart import AlbumArt
from scatterbrainz.model.albumartattempt import AlbumArtAttempt
from scatterbrainz.model.lyrics import Lyrics
from scatterbrainz.model.lyricsattempt import LyricsAttempt
from scatterbrainz.model.artistbio import ArtistBio
from scatterbrainz.model.albumsummary import AlbumSummary
from scatterbrainz.model.similarartist import SimilarArtist
from scatterbrainz.model.shopdownload import ShopDownload
from scatterbrainz.model.shopdownloadattempt import ShopDownloadAttempt

PGUuid = postgres.PGUuid

artist_albums = sa.Table('scatterbrainz_artist_albums', meta.metadata,
    sa.Column('artist_mbid', PGUuid, sa.ForeignKey('scatterbrainz_artists.artist_mbid')),
    sa.Column('release_group_mbid', PGUuid, sa.ForeignKey('scatterbrainz_albums.release_group_mbid'))
)


Artist.albums = orm.relation(Album, secondary=artist_albums, backref='artists')
Album.tracks = orm.relation(Track, backref='album')
Track.file = orm.relation(AudioFile, backref='track')
