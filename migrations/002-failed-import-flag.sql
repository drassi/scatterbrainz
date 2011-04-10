alter table scatterbrainz_downloads add column failed_import boolean NOT NULL default false;
alter table scatterbrainz_downloads add column import_trace character varying NULL;

