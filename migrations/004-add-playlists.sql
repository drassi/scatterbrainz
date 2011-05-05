create table scatterbrainz_playlists(
    playlist_id integer not null,
    owner_id integer not null,
    name character varying not null,
    created timestamp without time zone NOT NULL,
    modified timestamp without time zone NOT NULL,
    CONSTRAINT scatterbrainz_playlists_pkey PRIMARY KEY (playlist_id),
    CONSTRAINT scatterbrainz_playlists_owner_fkey FOREIGN KEY (owner_id) REFERENCES scatterbrainz_user (user_id),
    CONSTRAINT scatterbrainz_playlists_owner_name_uniq UNIQUE (owner_id, name)
);

create table scatterbrainz_playlist_items (
    playlist_id integer not null,
    track_id uuid not null,
    position integer not null,
    CONSTRAINT scatterbrainz_playlist_items_pkey PRIMARY KEY (playlist_id, position),
    CONSTRAINT scatterbrainz_playlist_items_playlist_fkey FOREIGN KEY (playlist_id) REFERENCES scatterbrainz_playlists (playlist_id),
    CONSTRAINT scatterbrainz_playlist_items_recording_mbid_fkey FOREIGN KEY (track_id) REFERENCES recording (gid)
);

create sequence scatterbrainz_playlists_playlist_id_seq;

