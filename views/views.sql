--LET THE FUN
  BEGIN;

CREATE TABLE scatterbrainz_artists_tmp AS (

  SELECT DISTINCT artist.gid           AS artist_mbid
                , artist_name.name     AS artist_name
                , sortname.name AS artist_sort_name
    FROM scatterbrainz_files
    JOIN release              ON release.gid = scatterbrainz_files.releasembid
    JOIN release_group        ON release_group.id = release.release_group
    JOIN recording            ON recording.gid = scatterbrainz_files.recordingmbid
    JOIN artist_credit        ON artist_credit.id = release_group.artist_credit
                              OR artist_credit.id = recording.artist_credit
    JOIN artist_credit_name   ON artist_credit.id = artist_credit_name.artist_credit
    JOIN artist               ON artist.id = artist_credit_name.artist
    JOIN artist_name          ON artist.name = artist_name.id
    JOIN artist_name sortname ON artist.sortname = sortname.id

);

ALTER TABLE scatterbrainz_artists_tmp
   ADD PRIMARY KEY (artist_mbid);

ALTER TABLE scatterbrainz_artists_tmp
   ADD CONSTRAINT artist_fk_mbid
   FOREIGN KEY (artist_mbid)
   REFERENCES artist(gid);

CREATE INDEX scatterbrainz_artists_search_tmp
    ON scatterbrainz_artists_tmp
 USING gin(to_tsvector('english', artist_name || ' ' || unaccent(artist_name)));


CREATE TABLE scatterbrainz_albums_tmp AS (

  SELECT DISTINCT release_group.gid                            AS release_group_mbid
	            , release_name.name                            AS release_group_name
	            , release_group_meta.firstreleasedate_year     AS release_group_year
	            , release_group_meta.firstreleasedate_month    AS release_group_month
	            , release_group_meta.firstreleasedate_day      AS release_group_day
	            , artist_name.name                             AS artist_credit_name
	            , release_name.name || ' ' || artist_name.name AS search
  FROM scatterbrainz_files
  JOIN release            ON release.gid = scatterbrainz_files.releasembid
  JOIN release_group      ON release_group.id = release.release_group
  JOIN release_name       ON release_group.name = release_name.id
  JOIN release_group_meta ON release_group.id = release_group_meta.id
  JOIN artist_credit      ON artist_credit.id = release_group.artist_credit
  JOIN artist_name        ON artist_credit.name = artist_name.id

);

ALTER TABLE scatterbrainz_albums_tmp
   ADD PRIMARY KEY (release_group_mbid);

ALTER TABLE scatterbrainz_albums_tmp
   ADD FOREIGN KEY (release_group_mbid)
   REFERENCES release_group(gid);

CREATE INDEX scatterbrainz_albums_search_tmp
    ON scatterbrainz_albums_tmp
 USING gin(to_tsvector('english', search || ' ' || unaccent(search)));


CREATE TABLE scatterbrainz_artist_albums_tmp AS (

  SELECT DISTINCT artist.gid        AS artist_mbid
                , release_group.gid AS release_group_mbid
     FROM scatterbrainz_files
     JOIN release             ON release.gid = scatterbrainz_files.releasembid
     JOIN release_group       ON release_group.id = release.release_group
     JOIN artist_credit       ON artist_credit.id = release_group.artist_credit
     JOIN artist_credit_name  ON artist_credit.id = artist_credit_name.artist_credit
     JOIN artist              ON artist_credit_name.artist = artist.id

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

 SELECT md5(release.gid || '_' || recording.gid || '_' ||
            track.position || '_' || medium.position) AS stable_id
       , scatterbrainz_files.id AS file_id
       , recording.gid          AS track_mbid
       , release_group.gid      AS release_group_mbid
       , track_name.name        AS track_name
       , track.position         AS track_number
       , medium.position        AS disc_number
       , release_name.name      AS release_name
       , artist_name.name       AS artist_credit_name
       , track_name.name || ' ' || rls_grp_name.name || ' ' || artist_name.name AS search
    FROM scatterbrainz_files
    JOIN recording                 ON recording.gid = scatterbrainz_files.recordingmbid
    JOIN release                   ON scatterbrainz_files.releasembid = release.gid
    JOIN medium                    ON medium.release = release.id
    JOIN tracklist                 ON medium.tracklist = tracklist.id
    JOIN track                     ON track.tracklist = tracklist.id
                                  AND track.recording = recording.id
    JOIN release_group             ON release_group.id = release.release_group
    JOIN track_name                ON track_name.id = recording.name
    JOIN release_name              ON release.name = release_name.id
    JOIN release_name rls_grp_name ON release_group.name = rls_grp_name.id
    JOIN artist_credit             ON artist_credit.id = track.artist_credit
    JOIN artist_name               ON artist_credit.name = artist_name.id

);

ALTER TABLE scatterbrainz_tracks_tmp
   ADD PRIMARY KEY (stable_id);

ALTER TABLE scatterbrainz_tracks_tmp
   ADD FOREIGN KEY (track_mbid)
   REFERENCES recording(gid);

ALTER TABLE scatterbrainz_tracks_tmp
   ADD FOREIGN KEY (release_group_mbid)
   REFERENCES scatterbrainz_albums_tmp(release_group_mbid);

CREATE INDEX scatterbrainz_tracks_search_tmp
    ON scatterbrainz_tracks_tmp
 USING gin(to_tsvector('english', search || ' ' || unaccent(search)));


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

ALTER INDEX scatterbrainz_artists_search_tmp RENAME TO scatterbrainz_artists_search;
ALTER INDEX scatterbrainz_album_idx_mbid_tmp RENAME TO scatterbrainz_album_idx_mbid;
ALTER INDEX scatterbrainz_release_group_idx_mbid_tmp RENAME TO scatterbrainz_release_group_idx_mbid;
ALTER INDEX scatterbrainz_albums_search_tmp RENAME TO scatterbrainz_albums_search;
ALTER INDEX scatterbrainz_track_idx_mbid_tmp RENAME TO scatterbrainz_track__idx_mbid;
ALTER INDEX scatterbrainz_tracks_release_group_idx_mbid_tmp RENAME TO scatterbrainz_tracks_release_group_idx_mbid;
ALTER INDEX scatterbrainz_tracks_search_tmp RENAME TO scatterbrainz_tracks_search;

COMMIT;

