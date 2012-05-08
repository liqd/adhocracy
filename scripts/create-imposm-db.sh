# run this as postgres user, eg:
# imp'${DB}'-pgsql > create_db.sh; sudo su postgres; sh ./create_db.sh
DBUSER='osm'
DB='imposm'
set -xe
#createuser --no-superuser --no-createrole --createdb ${DBUSER}
createdb -E UTF8 -O ${DBUSER} ${DB}
#createlang plpgsql ${DB}
psql -d ${DB} -f /usr/share/postgresql-9.1/contrib/postgis-1.5/postgis.sql
psql -d ${DB} -f /usr/share/postgresql-9.1/contrib/postgis-1.5/spatial_ref_sys.sql
#psql -d ${DB} -f /usr/lib64/python2.7/site-packages/imposm/900913.sql
echo "ALTER TABLE geometry_columns OWNER TO ${DBUSER}; ALTER TABLE spatial_ref_sys OWNER TO ${DBUSER};" | psql -d ${DB}
echo "ALTER USER ${DBUSER} WITH PASSWORD 'osm';" |psql -d ${DB}
echo "host	${DB}	${DBUSER}	127.0.0.1/32	md5" >> /etc/postgresql-9.1/pg_hba.conf
set +x
echo "Done. Don't forget to restart postgresql!"
