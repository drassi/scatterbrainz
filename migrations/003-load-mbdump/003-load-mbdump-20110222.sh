#!/bin/bash

# loads the 2011-02-22 musicbrainz snapshot

set -u
set -e

# Stuff to do manually once

# mkdir /tmp/musicbrainz
# cd /tmp/musicbrainz
# wget ftp://ftp.musicbrainz.org/pub/musicbrainz/data/ngs/xxx/mbdump.tar.bz2
# wget ftp://ftp.musicbrainz.org/pub/musicbrainz/data/ngs/xxx/mbdump-derived.tar.bz2
# 1130023c24cf1dbc70d5cf647854ee00 for 20110416-2/mbdump-derived.tar.bz2
# 91a663776b9875dd70b00a270cb3a403 for 20110416-2/mbdump.tar.bz2
# tar -xvf mbdump.tar.bz2
# tar -xvf mbdump-derived.tar.bz2

export APPDIR=/home/dan/dev/pylons/scatterbrainz/scatterbrainz
export MIGRATEDIR=$APPDIR/migrations/003-load-mbdump
export SNAPDIR=/tmp/musicbrainz/mbdump
export MBSQLDIR=/tmp/musicbrainz-server/admin/sql

# git clone git://git.musicbrainz.org/musicbrainz-server.git /tmp/musicbrainz-server
# git apply $APPDIR/musicbrainz-server.patch

# sudo su postgres
# export PGPASSWORD=xxx

# http://blog.hagander.net/archives/131-Automatically-dropping-and-creating-constraints.html
echo Generating scatterbrainz database constraint drop/create scripts
psql -t -U musicbrainz -f $MIGRATEDIR/generate_drop_constraints.sql | grep scatterbrainz > /tmp/drop_scatterbrainz_constraints.sql
psql -t -U musicbrainz -f $MIGRATEDIR/generate_create_constraints.sql | grep scatterbrainz > /tmp/create_scatterbrainz_constraints.sql

echo Running drop_scatterbrainz_constraints.sql
time psql -1 -U musicbrainz -f /tmp/drop_scatterbrainz_constraints.sql

echo Dropping all musicbrainz tables
time psql -t -U musicbrainz -c "select 'DROP TABLE ' || tablename || ' CASCADE;' from pg_tables where schemaname = 'public' and tablename not like 'scatterbrainz_%';" | psql -U musicbrainz

echo Creating all musicbrainz tables
time psql -U musicbrainz -f $MBSQLDIR/CreateTables.sql

export PGPASSWORD_TMP=$PGPASSWORD
export PGPASSWORD=
echo Copying in new musicbrainz snap
cd $SNAPDIR
for f in *; do
    echo $f:
    time psql -U postgres -d musicbrainz -c "copy $f from '/tmp/musicbrainz/mbdump/$f';"
done
export PGPASSWORD=$PGPASSWORD_TMP

echo Creating all musicbrainz pkeys, fkeys, indexes
time psql -U musicbrainz -f $MBSQLDIR/CreatePrimaryKeys.sql
time psql -U musicbrainz -f $MBSQLDIR/CreateIndexes.sql
time psql -U musicbrainz -f $MBSQLDIR/CreateFKConstraints.sql
time psql -U musicbrainz -f $MBSQLDIR/CreateSearchIndexes.sql

echo Fixing redirected mbids
python $MIGRATEDIR/generate_redirect_mbids.py | psql -U musicbrainz

echo Vacuum 1
time psql -U musicbrainz -c "VACUUM ANALYZE;"

echo Running create_scatterbrainz_constraints.sql
time psql -1 -U musicbrainz -f /tmp/create_scatterbrainz_constraints.sql

echo Re-building artist, album, track mviews
time psql -U musicbrainz -f $APPDIR/views/views.sql

echo Vacuum 2
time psql -U musicbrainz -c "VACUUM ANALYZE;"

