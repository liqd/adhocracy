def format_json_to_geotag(geotag):

    import geojson
    from geoalchemy.utils import to_wkt

    if geotag == '':
        return None

    else:
        return to_wkt(geojson.loads(geotag)['geometry'])
