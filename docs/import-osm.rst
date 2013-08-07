Import OpenStreetMap data into Adhocracy
========================================

The following instructions describe how to import OpenStreetMap data (currently
limited to administrative boundaries) into Adhocracy.

This is done outside of the Adhocracy environment.


Initialize imposm database
--------------------------

Imposm_ extracts data from raw OSM data files and puts them in a dedicated
Postgis database in order to not pollute the main Adhocracy database.


Required files:

* An OSM database extract, e.g. germany.osm.pbf (doesn't contain level 2
  boundaries, i.e. German border though) or europe.osm.pbf

* An imposm mapping file (e.g. etc/osm_mapping.py)


Setup a Postgis database as described in `initialize-postgis.rst`.


Import data with imposm
-----------------------

    imposm --read germany.osm.pbf
    imposm --write -d ${dbname} -p {dbport} -m etc/osm_mapping.py


The imported boundaries are are stored in ``geometry`` column of table
``osm_region``. The regions also contain a couple of other attributes
as defined in the imposm mapping file.


Copy regions into Adhocracy
---------------------------

A postgres superuser has to create the dblink extension via

    create extension dblink;


The normal user can then create a dblink connection

    select dblink_connect('dbname=${dbname}');

and copy the data (examples):

    insert into region (select id, name, admin_level, 'Bundesland', boundary from dblink('dbname=${dbname}', 'select osm_id, name,admin_level, geometry from osm_region where admin_level=4 and name is not null') as t1(id int, name text, admin_level int, boundary geometry));

    insert into region (select id, name, admin_level, 'Stadt', boundary from dblink('dbname=${dbname}', 'select osm_id, name, admin_level, geometry from osm_region where name=''Regensburg''') as t1(id int, name text, admin_level int, boundary geometry));

The value for column 4 (``admin_type``) is one of *Stadt*, *Gemeinde*,
*Bundesland* etc and needs to be mapped manually.


When using europe.osm.pbf you may not want to insert all European regions.
To exclude regions outside a specific region into Adhocracy use a statement
like the following:

    insert into region (select id, name, admin_level, 'Gemeinde', boundary from dblink('dbname=${dbname}', 'select b.osm_id, b.name, b.admin_level, b.geometry from osm_region a, osm_region b where a.osm_id != b.osm_id AND a.osm_id=62467 AND a.geometry is not null && b.geometry is not null AND ST_Contains(a.geometry, b.geometry) AND b.admin_level=8 AND b.name IS NOT NULL') as t1(id int, name text, admin_level int, boundary geometry));

This copies all admin_level=8 regions from Saxony.


Build region Hierarchy
----------------------

If Adhocracy is configured to show an instance select map on the main page (by
setting ``adhocracy.show_overview_map_on_index = True``), a region hierarchy is
used to allow querying cities within instance regions etc.


The following statement builds the region hierarchy by checking whether regions
contain each other:

    insert into region_hierarchy (inner_id, outer_id)
        select b.id, a.id from region a, region b where
            ST_Contains(a.boundary, b.boundary)
            AND a.id != b.id
            AND (a.admin_level=4 OR a.admin_level=5 OR a.admin_level=6 OR a.admin_level=7 OR a.admin_level=8);


To request the outer regions (of i.e. Guttau) use a inner join.

    select name,id
        from region inner join region_hierarchy
            on (region.id = region_hierarchy.outer_id)
            where region_hierarchy.inner_id=1309635;


Create regional instances
-------------------------

You can now prepopulate instances from regions. As an example, you may want to
have a look at the ``scripts/create-regional-instances.py`` script.


Update region centres
---------------------

To speed up initial buildup of instance centres, you can run the following
script:

    LD_LIBRARY_PATH=parts/geos/lib bin/adhocpy scripts/update-instance-geo_centres.py etc/adhocracy.ini


.. _Imposm: http://imposm.org/docs/imposm/latest/
