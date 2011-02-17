create table scatterbrainz_downloads
(
infohash character varying not null,
release_mbid uuid NOT NULL,
torrent_url character varying not null,
torrent_page_url character varying not null,
torrent_id character varying not null,
num_seeders integer not null,
file_json character varying not null,
started timestamp without time zone NOT NULL,
finished timestamp without time zone,
is_done boolean NOT NULL,
min_score double precision not null,
avg_score double precision not null,
owner_id integer not null,
CONSTRAINT scatterbrainz_downloads_owner_id_fkey FOREIGN KEY (owner_id)
      REFERENCES scatterbrainz_user (user_id),
CONSTRAINT scatterbrainz_downloads_pkey PRIMARY KEY (infohash),
CONSTRAINT scatterbrainz_downloads_release_mbid_fkey FOREIGN KEY (release_mbid) REFERENCES release (gid)
);


