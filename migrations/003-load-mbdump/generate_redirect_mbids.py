updates = [
    ('artist', 'scatterbrainz_artists', 'artist_mbid'),
    ('artist', 'scatterbrainz_artistbio', 'artist_mbid'),
    ('artist', 'scatterbrainz_similarartists', 'artist_mbid'),
    ('artist', 'scatterbrainz_similarartists', 'similar_artist_mbid'),
    ('artist', 'scatterbrainz_artist_albums', 'artist_mbid'),
    ('release_group', 'scatterbrainz_downloads', 'release_group_mbid'),
    ('release_group', 'scatterbrainz_downloadattempt', 'release_group_mbid'),
    ('release_group', 'scatterbrainz_albums', 'release_group_mbid'),
    ('release_group', 'scatterbrainz_tracks', 'release_group_mbid'),
    ('release_group', 'scatterbrainz_artist_albums', 'release_group_mbid'),
    ('release_group', 'scatterbrainz_albumsummary', 'release_group_mbid'),
    ('release_group', 'scatterbrainz_albumartattempt', 'release_group_mbid'),
    ('release_group', 'scatterbrainz_albumart', 'release_group_mbid'),
    ('release', 'scatterbrainz_downloads', 'release_mbid'),
    ('release', 'scatterbrainz_files', 'releasembid'),
    ('recording', 'scatterbrainz_tracks', 'track_mbid'),
    ('recording', 'scatterbrainz_lyrics', 'recording_mbid'),
    ('recording', 'scatterbrainz_lyricsattempt', 'recording_mbid'),
    ('recording', 'scatterbrainz_files', 'recordingmbid'),
]

print 'BEGIN;'

for (entity, table, column) in updates:
    print """
update {table} target
   set {column} = entity.gid
  from {entity}_gid_redirect redirect
     , {entity} entity
 where target.{column} = redirect.gid
   and redirect.new_id = entity.id;
""".format(entity=entity, table=table, column=column)

# Delete disappeared similar artist mbids
print """
delete from scatterbrainz_similarartists
 where similar_artist_mbid not in (
        select gid
          from artist
         where gid = similar_artist_mbid
 );
"""

# Delete disappeared artists
# 25f54bb7-c393-44e4-8e26-e4f4cd7aa61c = Queen & David Bowie
# 870c00b3-b06e-4baa-84e9-e436addf3150 = Air and Alessandro Baricco
for mbid in ['25f54bb7-c393-44e4-8e26-e4f4cd7aa61c',
             '870c00b3-b06e-4baa-84e9-e436addf3150']:
    for table in ['scatterbrainz_artists',
                  'scatterbrainz_artistbio',
                  'scatterbrainz_similarartists',
                  'scatterbrainz_artist_albums']:
        print "delete from {table} where artist_mbid = '{mbid}';".format(table=table, mbid=mbid)

print 'COMMIT;'

