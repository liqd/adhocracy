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

This usually works like

    psql -d adhocracy

    adhocracy=# create extension postgis;


But currently not, because postgis is not completely installed via buildout (to
be fixed), so we simply do:

    psql -d adhocracy -f parts/postgresql/share/contrib/postgis-2.0/postgis.sql


Change ownership of tables to adhocracy user
--------------------------------------------

Don't know if this is really needed.

    psql -d adhocracy

    adhocracy=# grant all privileges on database adhocracy to adhocracy;
    adhocracy=# grant all on table spatial_ref_sys to adhocracy;
    adhocracy=# grant all on table geometry_columns to adhocracy;
    adhocracy=# grant all on table geography_columns to adhocracy;
