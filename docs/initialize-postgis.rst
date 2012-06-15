Initialize Postgis with Geo extension
=====================================

The standard adhocracy buildout setup proposes to build postgres and postgis
locally.


Initialize local database cluster
---------------------------------

After installing postgres, a local database cluster has to be initialized.

    bin/pg_ctl -D var/postgresql/data init


Create postgres user
--------------------

In this example the user is called adhocracy.

    createuser --no-superuser --no-createrole --no-createdb adhocracy


Create database
---------------

In this example the database is called adhocracy.

    createdb -E UTF8 -O adhocracy adhocracy


Create postgis extension
------------------------

A postgres superuser has to install the postgis extension.


We do this with the following command:

    psql -d adhocracy -f parts/postgresql/share/contrib/postgis-2.0/postgis.sql


Because geoalchemy doesn't fully work with PostGIS 2.x yet, we remove PostGIS
functions which we don't need, which would otherwise result in an error because
of lack of explicit type casts by geoalchemy (see
https://trac.osgeo.org/postgis/ticket/1869):

    psql -d adhocracy -c "drop function st_asbinary (geography);"
    psql -d adhocracy -c "drop function st_asbinary (geography, text);"


.. note::

    Normally, the PostGIS extension can be installed with:

        psql -d adhocracy -c "create extension postgis;"

    But currently not, because
    
    - postgis is not completely installed via buildout (to be fixed)
    - of the geoalchemy incompatibility issue explained above.


Change ownership of tables to adhocracy user
--------------------------------------------

Don't know if this is really needed.

    psql -d adhocracy

    adhocracy=# grant all privileges on database adhocracy to adhocracy;
    adhocracy=# grant all on table spatial_ref_sys to adhocracy;
    adhocracy=# grant all on table geometry_columns to adhocracy;
    adhocracy=# grant all on table geography_columns to adhocracy;
