create sequence scatterbrainz_trackplays_seq;

create table scatterbrainz_trackplays(
    id integer not null default nextval('scatterbrainz_trackplays_seq'),
    user_id integer not null,
    track_mbid uuid not null,
    ip character varying not null,
    played timestamp without time zone NOT NULL,
    CONSTRAINT scatterbrainz_trackplays_pkey PRIMARY KEY (id),
    CONSTRAINT scatterbrainz_trackplays_user_fkey FOREIGN KEY (user_id) REFERENCES scatterbrainz_user (user_id),
    CONSTRAINT scatterbrainz_trackplays_track_fkey FOREIGN KEY (track_mbid) REFERENCES recording (gid)
);

