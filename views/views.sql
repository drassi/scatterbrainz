--LET THE FUN
  BEGIN;

CREATE TABLE scatterbrainz_artists_tmp AS (

  SELECT DISTINCT artist.gid           AS artist_mbid
                , artist_name.name     AS artist_name
                , artist_sortname.name AS artist_sort_name
    FROM scatterbrainz_files
    JOIN release ON release.gid = scatterbrainz_files.releasembid
    JOIN recording ON recording.gid = scatterbrainz_files.recordingmbid
    JOIN artist_credit ON artist_credit.id = release.artist_credit
                       OR artist_credit.id = recording.artist_credit
    JOIN artist_credit_name ON artist_credit.id = artist_credit_name.artist_credit
    JOIN artist ON artist.id = artist_credit_name.artist
    JOIN artist_name ON artist.name = artist_name.id
    JOIN artist_name artist_sortname ON artist.sortname = artist_sortname.id

);

ALTER TABLE scatterbrainz_artists_tmp
   ADD PRIMARY KEY (artist_mbid);

ALTER TABLE scatterbrainz_artists_tmp
   ADD CONSTRAINT artist_fk_mbid
   FOREIGN KEY (artist_mbid)
   REFERENCES artist(gid);

CREATE TABLE scatterbrainz_albums_tmp AS (

  SELECT   release_group.gid                       AS release_group_mbid
	, release_name.name                             AS release_group_name
	, release_group_meta.firstreleasedate_year      AS release_group_year
	, release_group_meta.firstreleasedate_month     AS release_group_month
	, release_group_meta.firstreleasedate_day       AS release_group_day
	, release_group_name.name || ' ' ||
	  array_to_string(array_agg(distinct artist_name.name), ' ')   AS search
     FROM release_group
     JOIN release              ON release_group.id = release.release_group
     JOIN scatterbrainz_files  ON release.gid = scatterbrainz_files.releasembid
     JOIN release_name         ON release_name.id = release_group.name
     JOIN release_name release_group_name ON release_group.name = release_group_name.id
     JOIN release_group_meta   ON release_group.id = release_group_meta.id
     JOIN artist_credit        ON artist_credit.id = release_group.artist_credit
     JOIN artist_credit_name   ON artist_credit.id = artist_credit_name.artist_credit
     JOIN artist_name          ON artist_credit_name.name = artist_name.id
 GROUP BY release_group.gid
	, release_name.name
	, release_group_meta.firstreleasedate_year
	, release_group_meta.firstreleasedate_month
	, release_group_meta.firstreleasedate_day
	, release_group_name.name

);

ALTER TABLE scatterbrainz_albums_tmp
   ADD PRIMARY KEY (release_group_mbid);

ALTER TABLE scatterbrainz_albums_tmp
   ADD FOREIGN KEY (release_group_mbid)
   REFERENCES release_group(gid);

CREATE TABLE scatterbrainz_artist_albums_tmp AS (

  SELECT DISTINCT artist.gid                                    AS artist_mbid
              , release_group.gid                             AS release_group_mbid
     FROM release_group
     JOIN release              ON release_group.id = release.release_group
     JOIN scatterbrainz_files  ON release.gid = scatterbrainz_files.releasembid
     JOIN artist_credit        ON artist_credit.id = release_group.artist_credit
     JOIN artist_credit_name   ON artist_credit.id = artist_credit_name.artist_credit
     JOIN artist               ON artist_credit_name.artist = artist.id

); 

ALTER TABLE scatterbrainz_artist_albums_tmp
   ADD FOREIGN KEY (artist_mbid)
   REFERENCES scatterbrainz_artists_tmp(artist_mbid);

ALTER TABLE scatterbrainz_artist_albums_tmp
   ADD FOREIGN KEY (release_group_mbid)
   REFERENCES scatterbrainz_albums_tmp(release_group_mbid);


CREATE INDEX scatterbrainz_album_idx_mbid_tmp ON scatterbrainz_artist_albums_tmp (artist_mbid);
CREATE INDEX scatterbrainz_release_group_idx_mbid_tmp ON scatterbrainz_artist_albums_tmp (release_group_mbid);

CREATE TABLE scatterbrainz_tracks_tmp AS (

  SELECT scatterbrainz_files.id AS file_id
       , recording.gid     AS track_mbid
       , release_group.gid AS release_group_mbid
       , track_name.name   AS track_name
       , track.position    AS track_number
       , medium.position   AS disc_number
       , release_name.name AS release_name
       , track_name.name || ' ' || release_group_name.name || ' ' ||
         array_to_string(array_agg(distinct artist_name.name), ' ')   AS search
    FROM scatterbrainz_files
    JOIN recording ON recording.gid = scatterbrainz_files.recordingmbid
    JOIN release on scatterbrainz_files.releasembid = release.gid
    JOIN medium on medium.release = release.id
    JOIN tracklist on medium.tracklist = tracklist.id
    JOIN track on track.tracklist = tracklist.id
              and track.recording = recording.id
    JOIN release_group ON release_group.id = release.release_group
    JOIN track_name ON track_name.id = recording.name
    JOIN release_name ON release.name = release_name.id
    JOIN release_name release_group_name ON release_group.name = release_group_name.id
    JOIN artist_credit        ON artist_credit.id = release_group.artist_credit
    JOIN artist_credit_name   ON artist_credit.id = artist_credit_name.artist_credit
    JOIN artist_name          ON artist_credit_name.name = artist_name.id
    GROUP BY recording.gid
           , track_name.name
           , track.position
           , release_group.gid
           , medium.position
           , release_name.name
           , release_group_name.name
           , scatterbrainz_files.id
);

ALTER TABLE scatterbrainz_tracks_tmp
   ADD PRIMARY KEY (file_id);

ALTER TABLE scatterbrainz_tracks_tmp
   ADD FOREIGN KEY (track_mbid)
   REFERENCES recording(gid);

ALTER TABLE scatterbrainz_tracks_tmp
   ADD FOREIGN KEY (release_group_mbid)
   REFERENCES scatterbrainz_albums_tmp(release_group_mbid);

CREATE INDEX scatterbrainz_track_idx_mbid_tmp ON scatterbrainz_tracks_tmp (track_mbid);
CREATE INDEX scatterbrainz_tracks_release_group_idx_mbid_tmp ON scatterbrainz_tracks_tmp (release_group_mbid);

DROP TABLE IF EXISTS scatterbrainz_tracks;
DROP TABLE IF EXISTS scatterbrainz_artist_albums;
DROP TABLE IF EXISTS scatterbrainz_albums;
DROP TABLE IF EXISTS scatterbrainz_artists;

ALTER TABLE scatterbrainz_artists_tmp RENAME TO scatterbrainz_artists;
ALTER TABLE scatterbrainz_albums_tmp RENAME TO scatterbrainz_albums;
ALTER TABLE scatterbrainz_tracks_tmp RENAME TO scatterbrainz_tracks;
ALTER TABLE scatterbrainz_artist_albums_tmp RENAME TO scatterbrainz_artist_albums;

ALTER INDEX scatterbrainz_album_idx_mbid_tmp RENAME TO scatterbrainz_album_idx_mbid;
ALTER INDEX scatterbrainz_release_group_idx_mbid_tmp RENAME TO scatterbrainz_release_group_idx_mbid;
ALTER INDEX scatterbrainz_track_idx_mbid_tmp RENAME TO scatterbrainz_track__idx_mbid;
ALTER INDEX scatterbrainz_tracks_release_group_idx_mbid_tmp RENAME TO scatterbrainz_tracks_release_group_idx_mbid;

COMMIT;

