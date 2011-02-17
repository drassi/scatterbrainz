from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import Column, Integer, String, Unicode, DateTime, Boolean, ForeignKey, SmallInteger, Text
from sqlalchemy import orm

from scatterbrainz.model.meta import metadata

from sqlalchemy.databases import postgres

PGUuid = postgres.PGUuid
Base = declarative_base(metadata=metadata)

class MBArtistName(Base):

    __tablename__ = 'artist_name'
    
    id = Column(u'id', Integer(), primary_key=True, nullable=False)
    name = Column(u'name', String(length=None, convert_unicode=False, assert_unicode=None), primary_key=False, nullable=False)

class MBArtist(Base):

    __tablename__ = 'artist'

    id = Column(u'id', Integer(), primary_key=True, nullable=False)
    gid = Column(u'gid', PGUuid(), primary_key=False, nullable=False)
    nameid = Column(u'name', Integer(), ForeignKey('artist_name.id'), primary_key=False, nullable=False)
    name = orm.relation(MBArtistName, primaryjoin=nameid==MBArtistName.id, backref='artists')
    sortnameid = Column(u'sort_name', Integer(), ForeignKey('artist_name.id'), primary_key=False, nullable=False)
    sortname = orm.relation(MBArtistName, primaryjoin=sortnameid==MBArtistName.id, backref='artistssort')
    begindate_year = Column(u'begin_date_year', SmallInteger(), primary_key=False)
    begindate_month = Column(u'begin_date_month', SmallInteger(), primary_key=False)
    begindate_day = Column(u'begin_date_day', SmallInteger(), primary_key=False)
    enddate_year = Column(u'end_date_year', SmallInteger(), primary_key=False)
    enddate_month = Column(u'end_date_month', SmallInteger(), primary_key=False)
    enddate_day = Column(u'end_date_day', SmallInteger(), primary_key=False)
    #typeid = Column(u'type', Integer(), ForeignKey('artist_type.id'), primary_key=False)
    #countryid = Column(u'country', Integer(), ForeignKey('country.id'), primary_key=False)
    #genderid = Column(u'gender', Integer(), ForeignKey('gender.id'), primary_key=False)
    comment = Column(u'comment', String(length=255, convert_unicode=False, assert_unicode=None), primary_key=False)
    #ipicode = Column(u'ipicode', String(length=11, convert_unicode=False, assert_unicode=None), primary_key=False)
    #editpending = Column(u'editpending', Integer(), primary_key=False, nullable=False)

class MBReleaseName(Base):
    
    __tablename__ = 'release_name'
    
    id = Column(u'id', Integer(), primary_key=True, nullable=False)
    name = Column(u'name', String(length=None, convert_unicode=False, assert_unicode=None), primary_key=False, nullable=False)

class MBArtistCredit(Base):

    __tablename__ = 'artist_credit'
    
    id = Column(u'id', Integer(), primary_key=True, nullable=False)
    nameid = Column(u'name', Integer(), ForeignKey('artist_name.id'), primary_key=False, nullable=False)
    name = orm.relation(MBArtistName, backref='artistcredits')
    artistcount = Column(u'artist_count', SmallInteger(), primary_key=False, nullable=False)
    refcount = Column(u'ref_count', Integer(), primary_key=False)

class MBArtistCreditName(Base):

    __tablename__ = 'artist_credit_name'
    
    artistcreditid = Column(u'artist_credit', Integer(), ForeignKey('artist_credit.id'), primary_key=True, nullable=False)
    artistcredit = orm.relation(MBArtistCredit)
    position = Column(u'position', SmallInteger(), primary_key=True, nullable=False)
    artistid = Column(u'artist', Integer(), ForeignKey('artist.id'), primary_key=False, nullable=False)
    artist = orm.relation(MBArtist)
    nameid = Column(u'name', Integer(), ForeignKey('artist_name.id'), primary_key=False, nullable=False)
    name = orm.relation(MBArtistName)
    joinphrase = Column(u'join_phrase', String(length=32, convert_unicode=False, assert_unicode=None), primary_key=False)

class MBReleaseGroupType(Base):

    __tablename__ = 'release_group_type'

    id = Column(u'id', Integer(), primary_key=True, nullable=False)
    name = Column(u'name', String(length=255, convert_unicode=False, assert_unicode=None), primary_key=False, nullable=False)

class MBReleaseGroup(Base):

    __tablename__ = 'release_group'

    id = Column(u'id', Integer(), primary_key=True, nullable=False)
    gid = Column(u'gid', PGUuid(), primary_key=False, nullable=False)
    nameid = Column(u'name', Integer(), ForeignKey('release_name.id'), primary_key=False, nullable=False)
    name = orm.relation(MBReleaseName, backref='releasegroups')
    artistcreditid = Column(u'artist_credit', Integer(), ForeignKey('artist_credit.id'), primary_key=False, nullable=False)
    artistcredit = orm.relation(MBArtistCredit, backref='releasegroups')
    typeid = Column(u'type', Integer(), ForeignKey('release_group_type.id'), primary_key=False)
    releasegrouptype = orm.relation(MBReleaseGroupType)
    comment = Column(u'comment', String(length=255, convert_unicode=False, assert_unicode=None), primary_key=False)
    #editpending = Column(u'editpending', Integer(), primary_key=False, nullable=False)

class MBReleaseGroupMeta(Base):

    __tablename__ = 'release_group_meta'

    id = Column(u'id', Integer(), ForeignKey('release_group.id'), primary_key=True, nullable=False)
    releasegroup = orm.relation(MBReleaseGroup, backref='meta')
    releasecount = Column(u'release_count', Integer(), primary_key=False, nullable=False)
    year = Column(u'first_release_date_year', SmallInteger(), primary_key=False)
    month = Column(u'first_release_date_month', SmallInteger(), primary_key=False)
    day = Column(u'first_release_date_day', SmallInteger(), primary_key=False)
    rating = Column(u'rating', SmallInteger(), primary_key=False)
    ratingcount = Column(u'rating_count', Integer(), primary_key=False)

class MBRelease(Base):

    __tablename__ = 'release'
    
    id = Column(u'id', Integer(), primary_key=True, nullable=False)
    gid = Column(u'gid', PGUuid(), primary_key=False, nullable=False)
    nameid = Column(u'name', Integer(), ForeignKey('release_name.id'), primary_key=False, nullable=False)
    name = orm.relation(MBReleaseName, backref='releases')
    artistcreditid = Column(u'artist_credit', Integer(), ForeignKey('artist_credit.id'), primary_key=False, nullable=False)
    artistcredit = orm.relation(MBArtistCredit, backref='releases')
    releasegroupid = Column(u'release_group', Integer(), ForeignKey('release_group.id'), primary_key=False, nullable=False)
    releasegroup = orm.relation(MBReleaseGroup, backref='releases')
    #statusid = Column(u'status', Integer(), ForeignKey('release_status.id'), primary_key=False)
    #packagingid = Column(u'packaging', Integer(), ForeignKey('release_packaging.id'), primary_key=False)
    #countryid = Column(u'country', Integer(), ForeignKey('country.id'), primary_key=False)
    #languageid = Column(u'language', Integer(), ForeignKey('language.id'), primary_key=False)
    #scriptid = Column(u'script', Integer(), ForeignKey('script.id'), primary_key=False)
    dateyear = Column(u'date_year', SmallInteger(), primary_key=False)
    datemonth = Column(u'date_month', SmallInteger(), primary_key=False)
    dateday = Column(u'date_day', SmallInteger(), primary_key=False)
    barcode = Column(u'barcode', String(length=255, convert_unicode=False, assert_unicode=None), primary_key=False)
    comment = Column(u'comment', String(length=255, convert_unicode=False, assert_unicode=None), primary_key=False)
    #editpending = Column(u'editpending', Integer(), primary_key=False, nullable=False)
    quality = Column(u'quality', SmallInteger(), primary_key=False, nullable=False)

class MBTrackName(Base):

    __tablename__ = 'track_name'

    id = Column(u'id', Integer(), primary_key=True, nullable=False)
    name = Column(u'name', String(length=None, convert_unicode=False, assert_unicode=None), primary_key=False, nullable=False)

class MBRecording(Base):

    __tablename__ = 'recording'
    
    id = Column(u'id', Integer(), primary_key=True, nullable=False)
    gid = Column(u'gid', PGUuid(), primary_key=False, nullable=False)
    nameid = Column(u'name', Integer(), ForeignKey('track_name.id'), primary_key=False, nullable=False)
    name = orm.relation(MBTrackName, backref='recordings')
    artistcreditid = Column(u'artist_credit', Integer(), ForeignKey('artist_credit.id'), primary_key=False, nullable=False)
    artistcredit = orm.relation(MBArtistCredit, backref='recordings')
    length = Column(u'length', Integer(), primary_key=False)
    comment = Column(u'comment', String(length=255, convert_unicode=False, assert_unicode=None), primary_key=False)
    #editpending = Column(u'editpending', Integer(), primary_key=False, nullable=False)

class MBRecordingGIDRedirect(Base):

    __tablename__ = 'recording_gid_redirect'
    
    gid = Column(u'gid', PGUuid(), primary_key=True, nullable=False)
    recordingid = Column(u'new_id', Integer(), ForeignKey('recording.id'), primary_key=False, nullable=False)
    recording = orm.relation(MBRecording)

class MBReleaseGIDRedirect(Base):

    __tablename__ = 'release_gid_redirect'
    
    gid = Column(u'gid', PGUuid(), primary_key=True, nullable=False)
    recordingid = Column(u'new_id', Integer(), ForeignKey('release.id'), primary_key=False, nullable=False)
    recording = orm.relation(MBRelease)

class MBTrackList(Base):

    __tablename__ = 'tracklist'
    
    id = Column(u'id', Integer(), primary_key=True, nullable=False)
    trackcount = Column(u'track_count', Integer(), primary_key=False, nullable=False)

class MBTrack(Base):

    __tablename__ = 'track'
    
    id = Column(u'id', Integer(), primary_key=True, nullable=False)
    recordingid = Column(u'recording', Integer(), ForeignKey('recording.id'), primary_key=False, nullable=False)
    recording = orm.relation(MBRecording)
    tracklistid = Column(u'tracklist', Integer(), ForeignKey('tracklist.id'), primary_key=False, nullable=False)
    tracklist = orm.relation(MBTrackList)
    position = Column(u'position', Integer(), primary_key=False, nullable=False)
    nameid = Column(u'name', Integer(), ForeignKey('track_name.id'), primary_key=False, nullable=False)
    name = orm.relation(MBTrackName)
    artistcreditid = Column(u'artist_credit', Integer(), ForeignKey('artist_credit.id'), primary_key=False, nullable=False)
    artistcredit = orm.relation(MBArtistCredit)
    length = Column(u'length', Integer(), primary_key=False)
    #editpending = Column(u'editpending', Integer(), primary_key=False, nullable=False)

class MBMedium(Base):

    __tablename__ = 'medium'
    
    id = Column(u'id', Integer(), primary_key=True, nullable=False)
    tracklistid = Column(u'tracklist', Integer(), ForeignKey('tracklist.id'), primary_key=False, nullable=False)
    tracklist = orm.relation(MBTrackList)
    releaseid = Column(u'release', Integer(), ForeignKey('release.id'), primary_key=False, nullable=False)
    release = orm.relation(MBRelease)
    position = Column(u'position', Integer(), primary_key=False, nullable=False)
    formatid = Column(u'format', Integer(), primary_key=False)
    name = Column(u'name', String(length=255, convert_unicode=False, assert_unicode=None), primary_key=False)
    #editpending = Column(u'editpending', Integer(), primary_key=False, nullable=False)

class MBLinkType(Base):

    __tablename__ = 'link_type'
    
    id = Column(u'id', Integer(), primary_key=True, nullable=False)
    Column(u'parent', Integer(), ForeignKey('link_type.id'), primary_key=False)
    Column(u'child_order', Integer(), primary_key=False, nullable=False)
    Column(u'gid', PGUuid(), primary_key=False, nullable=False)
    Column(u'entity_type0', String(length=50, convert_unicode=False, assert_unicode=None), primary_key=False)
    Column(u'entity_type1', String(length=50, convert_unicode=False, assert_unicode=None), primary_key=False)
    name = Column(u'name', String(length=255, convert_unicode=False, assert_unicode=None), primary_key=False, nullable=False)
    Column(u'description', Text(length=None, convert_unicode=False, assert_unicode=None), primary_key=False)
    linkphrase = Column(u'link_phrase', String(length=255, convert_unicode=False, assert_unicode=None), primary_key=False, nullable=False)
    rlinkphrase = Column(u'reverse_link_phrase', String(length=255, convert_unicode=False, assert_unicode=None), primary_key=False, nullable=False)
    Column(u'short_link_phrase', String(length=255, convert_unicode=False, assert_unicode=None), primary_key=False, nullable=False)
    Column(u'priority', Integer(), primary_key=False, nullable=False)

class MBLink(Base):

    __tablename__ = 'link'

    id = Column(u'id', Integer(), primary_key=True, nullable=False)
    link_type_id = Column(u'link_type', Integer(), ForeignKey('link_type.id'), primary_key=False, nullable=False)
    link_type = orm.relation(MBLinkType)
    beginyear = Column(u'begin_date_year', SmallInteger(), primary_key=False)
    beginmonth = Column(u'begin_date_month', SmallInteger(), primary_key=False)
    beginday = Column(u'begin_date_day', SmallInteger(), primary_key=False)
    endyear = Column(u'end_date_year', SmallInteger(), primary_key=False)
    endmonth = Column(u'end_date_month', SmallInteger(), primary_key=False)
    endday = Column(u'end_date_day', SmallInteger(), primary_key=False)
    Column(u'attribute_count', Integer(), primary_key=False, nullable=False)

class MBLArtistURL(Base):

    __tablename__ = 'l_artist_url'
    
    id = Column(u'id', Integer(), primary_key=True, nullable=False)
    link_id = Column(u'link', Integer(), ForeignKey('link.id'), primary_key=False, nullable=False)
    artist_id = Column(u'entity0', Integer(), ForeignKey('artist.id'), primary_key=False, nullable=False)
    url_id = Column(u'entity1', Integer(), ForeignKey('url.id'), primary_key=False, nullable=False)
    #Column(u'editpending', Integer(), primary_key=False, nullable=False)

class MBLReleaseGroupURL(Base):

    __tablename__ = 'l_release_group_url'

    id = Column(u'id', Integer(), primary_key=True, nullable=False)
    link_id = Column(u'link', Integer(), ForeignKey('link.id'), primary_key=False, nullable=False)
    release_group_id = Column(u'entity0', Integer(), ForeignKey('release_group.id'), primary_key=False, nullable=False)
    url_id = Column(u'entity1', Integer(), ForeignKey('url.id'), primary_key=False, nullable=False)
    #Column(u'editpending', Integer(), primary_key=False, nullable=False)

class MBLReleaseURL(Base):

    __tablename__ = 'l_release_url'

    id = Column(u'id', Integer(), primary_key=True, nullable=False)
    link_id = Column(u'link', Integer(), ForeignKey('link.id'), primary_key=False, nullable=False)
    release_group_id = Column(u'entity0', Integer(), ForeignKey('release.id'), primary_key=False, nullable=False)
    url_id = Column(u'entity1', Integer(), ForeignKey('url.id'), primary_key=False, nullable=False)
    Column(u'editpending', Integer(), primary_key=False, nullable=False)

class MBLArtistArtist(Base):
    
    __tablename__ = 'l_artist_artist'
    
    id = Column(u'id', Integer(), primary_key=True, nullable=False)
    link_id = Column(u'link', Integer(), ForeignKey('link.id'), primary_key=False, nullable=False)
    link = orm.relation(MBLink)
    artist1_id = Column(u'entity0', Integer(), ForeignKey('artist.id'), primary_key=False, nullable=False)
    artist1 = orm.relation(MBArtist, primaryjoin=artist1_id==MBArtist.id)
    artist2_id = Column(u'entity1', Integer(), ForeignKey('artist.id'), primary_key=False, nullable=False)
    artist2 = orm.relation(MBArtist, primaryjoin=artist2_id==MBArtist.id)
    Column(u'editpending', Integer(), primary_key=False, nullable=False)

class MBURL(Base):

    __tablename__ = 'url'
    
    id = Column(u'id', Integer(), primary_key=True, nullable=False)
    Column(u'gid', PGUuid(), primary_key=False, nullable=False)
    url = Column(u'url', Text(length=None, convert_unicode=False, assert_unicode=None), primary_key=False, nullable=False)
    Column(u'description', Text(length=None, convert_unicode=False, assert_unicode=None), primary_key=False)
    Column(u'ref_count', Integer(), primary_key=False, nullable=False)
    #Column(u'editpending', Integer(), primary_key=False, nullable=False)
    
