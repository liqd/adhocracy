/*jslint vars:true, browser:true, nomen:true */
/*global popup:true, $:true*/

/*
 * Two VectorLayers for each admin_level, one for simplified polygons
 and one for polygons in full complexity

 * BBox Strategy to fetch features dynamically by bounding box

 * Cluster-Strategy to simplify polygons on client additionally. The 
 Strategy replaces all features within a certain number of pixels with
 a new one.
 NOTE: check polygon support
 NOTE: tries to fetch "http://${base_url}/undefined"

 * configure admin_levels and different styles for each admin_level 
 on every zoom level. styles are 0 for hidden, 1 for borders and 
 2 for areas. configure baseurl.

 * requires openlayers/lib/OpenLayers.js at baseurl

 * TODO: capitol markers with popup -> link to instance
 * TODO: list of search matches/proposals
 * TODO: hover (see cluster strategy example)

 * TODO: list of all open popups
 * TODO: adjust proposal size
 */

var popup;

var styleProps = {
    pointRadius: 5,
    fillColor: "#f28686",
    fillOpacity: 0.8,
    strokeColor: "#be413f",
    strokeWidth: 1,
    strokeOpacity: 0.8
};

var styleSelect = { 
    pointRadius: 5,
    fillColor: "#e82b2b",
    fillOpacity: 0.8,
    strokeColor: "#be413f",
    strokeWidth: 1,
    strokeOpacity: 0.8
};

var styleBorder = {
    fillColor: "#ffcc66",
    fillOpacity: 0.5,
    strokeColor: "#ff9933"
};

var styleArea = {
    fillColor: "#66ccff",
    fillOpacity: 0.5,
    strokeColor: "#3399ff"
};



function createProposalLayer() {

    return new OpenLayers.Layer.Vector("proposal", {
        displayInLayerSwitcher: false, 
	projection: new OpenLayers.Projection("EPSG:4326"),
        styleMap: new OpenLayers.StyleMap({'default': new OpenLayers.Style(styleProps),
                					   'select': new OpenLayers.Style(styleSelect)}) 
    });
}

function fetchSingleProposal(singleProposalId, layer, callback) {
    var url = '/proposal/' + singleProposalId + '/get_geotag';
    $.ajax({
        url: url,
        success: function(data) {
            var features = new OpenLayers.Format.GeoJSON({}).read(data);
            if (features) {
                // assert(features.length==1);
                var feature = features[0];
                $('#proposal_geotag_field').val(new OpenLayers.Format.GeoJSON({}).write(feature));
                feature.geometry.transform(new OpenLayers.Projection("EPSG:4326"), new OpenLayers.Projection("EPSG:900913"));
                layer.addFeatures([feature]);
                callback(feature);
            } else {
                callback(null);
            }
        },
        error: function(xhr,err){
	    //console.log('No response from server, sorry. url: ' + url + ', Error: '+err);
            //alert('No response from server, sorry. Error: '+err);
        }
    })
}


function createOverviewLayer() {

    return new OpenLayers.Layer.Vector('overview', {
        strategies: [new OpenLayers.Strategy.Fixed()],
        protocol: new OpenLayers.Protocol.HTTP({
            url: '/instance/get_instance_regions',
            format: new OpenLayers.Format.GeoJSON()
        }),
        projection: new OpenLayers.Projection("EPSG:4326"),
        styleMap: new OpenLayers.StyleMap({'default': new OpenLayers.Style(styleBorder)})
    })

}


function createRegionProposalsLayer(instanceKey, initialProposals, featuresAddedCallback) {

    var rule = new OpenLayers.Rule({
        symbolizer: {
            graphicHeight: 31,
            graphicWidth: 24,
            graphicYOffset: -31
        }
    })

    rule.evaluate = function (feature) {
        if (initialProposals) {
            var index = initialProposals.indexOf(feature.fid);

            if (index >= 0) {
                var letter = String.fromCharCode(index+97);
                this.symbolizer.externalGraphic = '/images/map_marker_pink_'+letter+'.png';
                $('#result_list_marker_'+feature.fid).attr('alt', letter).addClass('marker_'+letter);
            
                return true;
            } else {
                return false;
            }
        }
        return false;
    }

    var layer = new OpenLayers.Layer.Vector('region_proposals', {
        strategies: [new OpenLayers.Strategy.Fixed()],
        protocol: new OpenLayers.Protocol.HTTP({
            url: '/instance/' + instanceKey + '/get_proposal_geotags',
            format: new OpenLayers.Format.GeoJSON()
        }),
        projection: new OpenLayers.Projection("EPSG:4326"),
        styleMap: new OpenLayers.StyleMap({
            'default': new OpenLayers.Style(styleProps, {rules: [
                rule,
                new OpenLayers.Rule({elseFilter: true})
            ]}),
            'select': new OpenLayers.Style(styleSelect)
        }),
    })

    layer.events.on({
        'featuresadded': featuresAddedCallback
    })

    return layer
}


function createPopupControl(layer, buildPopupContent) {

    layer.events.on({
        'featureselected': function(feature) {
            popup = new OpenLayers.Popup.FramedCloud("singlepopup",
                feature.feature.geometry.getBounds().getCenterLonLat(),
                null,
                buildPopupContent(feature.feature.attributes),
                null,false,null
                );
            this.map.addPopup(popup);
        },
        'featureunselected': function(feature) {
            this.map.removePopup(popup);
        }
    });

    var selectControl = new OpenLayers.Control.SelectFeature(layer, {
            clickout: true,
            toggle: false,
            multiple: false,
            hover: false,
            toggleKey: "ctrlKey", // ctrl key removes from selection
            multipleKey: "shiftKey", // shift key adds to selection
            box: false,
            autoActivate: true,
        });

    return selectControl;
}

function addEditControls(map, layer) {

    var buttonState;

    var pointControl = new OpenLayers.Control.DrawFeature(layer, OpenLayers.Handler.Point, {
        featureAdded: function(feature) {pointClicked()}
    });
    
    function updateEditButtons() {

        var new_state = layer.features.length;

        if (buttonState != new_state) {
            
            if (buttonState == 0) {
                addChangeRemoveGeoButton(layer, pointControl);
                $('#add_geo_button').remove();
            } else {
                addAddGeoButton();
                $('#change_geo_button').remove();
                $('#remove_geo_button').remove();
            }
            buttonState = new_state;
        }
    }

    function addAddGeoButton() {
        $('<a />', {
            id: 'add_geo_button',
            class: 'button',
            click: function() {
                //propslayer. OpenLayers.Handler.Click({single:true, stopSingle:true});
                pointControl.activate();
            },
            // FIXME: Use Gettext
            // text: 'Add position'
            text: 'Setze Position'
        }).appendTo('#edit_map_buttons');
    }

    function addChangeRemoveGeoButton() {
        $('<a />', {
            id: 'change_geo_button',
            class: 'button',
            click: function() {
                //propslayer. OpenLayers.Handler.Click({single:true, stopSingle:true});
                layer.removeAllFeatures();
                pointControl.activate();
            },
            // FIXME: Use Gettext
            // text: 'Set different position'
            text: 'Setze andere Position'
        }).appendTo('#edit_map_buttons');

        $('<a />', {
            id: 'remove_geo_button',
            class: 'button',
            click: function() {
                layer.removeAllFeatures();
                $('#proposal_geotag_field').val('');
                updateEditButtons();
            },
            // FIXME: Use Gettext
            // text: 'Remove position'
            text: 'Entferne Position'
        }).appendTo('#edit_map_buttons');
    }

    function updateGeotagField() {
        var transformed_feature = layer.features[0].clone();
        transformed_feature.geometry.transform(new OpenLayers.Projection("EPSG:900913"), new OpenLayers.Projection("EPSG:4326"));
        $('#proposal_geotag_field').val(new OpenLayers.Format.GeoJSON({}).write(transformed_feature));
        map.setCenter(layer.features[0].geometry.getBounds().getCenterLonLat(), 
                      map.getZoom());
    }

    function pointClicked() {
        pointControl.deactivate();
        updateEditButtons();
        updateGeotagField();
    }

    function singleProposalFetched(feature) {
        if (feature) {
            addChangeRemoveGeoButton(layer, pointControl);
            buttonState = 1;
        } else {
            addAddGeoButton(pointControl);
            buttonState = 0;
        }
    }

    map.addControls([
        new OpenLayers.Control.DragFeature(layer, {
            onComplete: function(feature, pixel) {
                updateGeotagField();
            },
            autoActivate: true
        }),
        pointControl
    ]);

    return singleProposalFetched;
}


function createRegionBoundaryLayer(instanceKey, callback) {

    var layer = new OpenLayers.Layer.Vector('instance_boundary', {
        displayInLayerSwitcher: false, 
        projection: new OpenLayers.Projection("EPSG:4326"),
        styleMap: new OpenLayers.StyleMap({'default': new OpenLayers.Style(styleBorder)}),
    })

    var url = '/instance/' + instanceKey + '/get_region'; 
    $.ajax({
        url: url,
        success: function(data) {
            var features = new OpenLayers.Format.GeoJSON({}).read(data);
            if (features) {
                // assert(features.length==1);
                var feature = features[0];
                feature.geometry.transform(new OpenLayers.Projection("EPSG:4326"), new OpenLayers.Projection("EPSG:900913"));
                layer.addFeatures([feature]);
                callback(feature);
            } else {
                callback(null);
            }
        },
        error: function(xhr,err){
	    //console.log('No response from server, sorry. url: ' + url + ', Error: '+err);
            //alert('No response from server, sorry. Error: '+err);
        }
    });

    return layer;
}

function addMultiBoundaryLayer(map) {

    var baseUrl = "/blub";
    var adminLevels = [2,4,5,6,8];
    var layers = new Array();

    //Zoom 0 ... 15 -> 0=hidden,1=visibleByBorder,2=visibleByArea,3=both
    var displayMap = [
        {styles: [0,0,0,0,2]},
        {styles: [0,0,0,0,2]},
        {styles: [1,0,0,0,2]},
        {styles: [1,0,0,0,2]},
        {styles: [1,1,0,0,2]},
        {styles: [1,1,0,0,2]},
        {styles: [1,1,1,0,2]},
        {styles: [1,1,1,0,2]},
        {styles: [1,1,1,0,2]},
        {styles: [1,1,1,1,2]},
        {styles: [1,1,1,1,2]},
        {styles: [1,1,1,1,1]},
        {styles: [1,1,1,1,1]},
        {styles: [1,1,1,1,1]},
        {styles: [1,1,1,1,1]},
        {styles: [1,1,1,1,1]},
        {styles: [1,1,1,1,1]},
        {styles: [1,1,1,1,1]},
        {styles: [1,1,1,1,1]}
    ];

    var moveTo = function(bounds, zoomChanged, dragging) {
        var zoom = map.getZoom();
        if (zoomChanged != null) {
            var i=0;
            while (i<adminLevels.length) {
                var styleChanged = displayMap[zoomChanged]['styles'][i];
                var style = displayMap[zoom]['styles'][i];
                if (styleChanged == 0) {
                    layers[i][0].setVisibility(false);
                    layers[i][1].setVisibility(false);
                } else {
                    if (zoomChanged < 8) {
                        layers[i][0].setVisibility(true);
                        layers[i][1].setVisibility(false);
                    } else {
                        layers[i][0].setVisibility(false);
                        layers[i][1].setVisibility(true);
                    }
                    if (style != styleChanged) {
                        if (styleChanged < 2) {
                            layers[i][0].styleMap['default'] 
                                = new OpenLayers.Style(styleBorder);
                            layers[i][1].styleMap['default'] 
                                = new OpenLayers.Style(styleBorder);	
                            redrawFeatures(layers[i][0],styleBorder);
                            redrawFeatures(layers[i][1],styleBorder);

                        } else {
                            layers[i][0].styleMap['default'] 
                                = new OpenLayers.Style(styleArea);	
                            layers[i][1].styleMap['default'] 
                                = new OpenLayers.Style(styleArea);	
                            redrawFeatures(layers[i][0],styleArea);
                            redrawFeatures(layers[i][1],styleArea);
                        }
                    }
                }
                i++;
            }
        }

        OpenLayers.Map.prototype.moveTo.apply(this, arguments);
    }

    function redrawFeatures(thelayer,thestyle) {
        var i=0;
        for (i=0; i<thelayer.features.length;i++) {
           thelayer.features[i].style = thestyle;
           var drawn = thelayer.drawFeature(thelayer.features[i],thestyle);
        } 
    }

    var layersIdx = 0;
    while (layersIdx < adminLevels.length) {
        var style = displayMap[map.getZoom()]['styles'][layersIdx];

        layers[layersIdx] = new Array(2);
        var complexity;
        for (complexity = 0; complexity < 2; complexity++) {
            var layername = "layer" + adminLevels[layersIdx] //or aname from config
                + (complexity == 0 ? 's' : 'c');
            //			var featureUrl = baseUrl + '/'
            //			          + (complexity == 0 ? 'simple' : 'full')
            //                                  + '.json';

            var featureUrl = baseUrl + '/' + adminLevels[layersIdx] + '/'
                + (complexity == 0 ? 'simple' : 'full')
                + '.json';

            layers[layersIdx][complexity] 
                = new OpenLayers.Layer.Vector(layername, {
                    displayInLayerSwitcher: false, 
                    strategies: [new OpenLayers.Strategy.BBOX()],
                    protocol: new OpenLayers.Protocol.HTTP({
                        url: featureUrl,
                        params: {
                            admin_level: adminLevels[layersIdx]
                        },
                        format: new OpenLayers.Format.GeoJSON({
                            ignoreExtraDims: true
                        })
                    }),
                    projection: new OpenLayers.Projection("EPSG:4326"),
                    styleMap: new OpenLayers.StyleMap({'default':(style < 2 ? new OpenLayers.Style(styleBorder) : new OpenLayers.Style(styleArea))})
                });
            //console.log(layers[layersIdx][complexity] != null);
            map.addLayer(layers[layersIdx][complexity]);
        }
        layersIdx++;
    }
    map.moveTo = moveTo;
}


function createBaseLayers(blank) {

    var baseLayers = [
        new OpenLayers.Layer.OSM("Public Transport",
                    "http://a.tile2.opencyclemap.org/transport/${z}/${x}/${y}.png"),
        new OpenLayers.Layer.OSM("Transport Map",
                    "http://otile1.mqcdn.com/tiles/1.0.0./osm/${z}/${x}/${y}.png"),
        //default Openstreetmap Baselayer
        new OpenLayers.Layer.OSM("Open Street Map"),
        new OpenLayers.Layer.OSM("&Ouml;pnv Deutschland", 
                    "http://tile.xn--pnvkarte-m4a.de/tilegen/${z}/${x}/${y}.png")
            ];

    // Blank Baselayer
    if (blank) {
        baseLayers.push(new OpenLayers.Layer("Blank",{isBaseLayer: true}));
    }

    //some Google Baselayers
    //		map.addLayer(new OpenLayers.Layer.Google("Google", {"sphericalMercator": true})); 
    /*	
        map.addLayer(new OpenLayers.Layer.Google(
        "Google Physical",
        {type: G_PHYSICAL_MAP}
        ));
        var gmap = new OpenLayers.Layer.Google(
        "Google Streets", // the default
        {numZoomLevels: 20}
        );
        var ghyb = new OpenLayers.Layer.Google(
        "Google Hybrid",
        {type: G_HYBRID_MAP, numZoomLevels: 20}
        );
        var gsat = new OpenLayers.Layer.Google(
        "Google Satellite",
        {type: G_SATELLITE_MAP, numZoomLevels: 22}
        );
        */
    /*
       var wmsLayer = new OpenLayers.Layer.WMS(
       "OpenLayers WMS", 
       "http://vmap0.tiles.osgeo.org/wms/vmap0",
       {layers: 'basic'}
       ); 
       map.addLayer(wmslayer);
       */

    return baseLayers;
}


function createMap(numZoomLevels) {

    return new OpenLayers.Map('map', {
        //restrictedExtent: new OpenLayers.Bounds(-180, -90, 180, 90),
        maxExtent: new OpenLayers.Bounds(-20037508.34,-20037508.34,
                                         20037508.34,20037508.34),
        maxResolution: 156543.0399,
        numZoomLevels: numZoomLevels,
        units: 'm',
        //projection: new OpenLayers.Projection("EPSG:900913"),
        //displayProjection: new OpenLayers.Projection("EPSG:4326"),
        projection: new OpenLayers.Projection("EPSG:4326"),
        controls: []
    });
}


function createControls(fullControls) {
    // add map controls

    var mapControls = [
        new OpenLayers.Control.Navigation(),
        new OpenLayers.Control.ScaleLine(),
    ];

    if (fullControls) {
        mapControls.push(new OpenLayers.Control.PanZoomBar());
        mapControls.push(new OpenLayers.Control.LayerSwitcher({'ascending':false}));
        // MousePosition currently displays 900913 instead of 4236
        mapControls.push(new OpenLayers.Control.MousePosition());
        // use KeyboardDefault only when map is the central element
        mapControls.push(new OpenLayers.Control.KeyboardDefaults());
        mapControls.push(new OpenLayers.Control.Scale());
    }

    return mapControls;
}



function centerMap(map, feature, boundary) {
    if (feature) {
        map.setCenter(feature.geometry.getBounds().getCenterLonLat(), 10);
        // x boundary
    } else {
        map.setCenter(feature.geometry.getBounds().getCenterLonLat(), 10);
        // nur boundary
    }
}


function createWaiter(number, callback) {

    // waits for number of addGeometry calls and finally calls callback

    var countdown = number;
    var bounds = new OpenLayers.Bounds();
    var is_empty = true;

    function addFeature(feature) {
        countdown--;

        if (feature) {
            bounds.extend(feature.geometry.getBounds());
            is_empty = false;
        }

        if (countdown == 0) {
            if (is_empty) {
                bounds = new OpenLayers.Bounds.fromArray(FALLBACK_BOUNDS).transform(new OpenLayers.Projection("EPSG:4326"), new OpenLayers.Projection("EPSG:900913"));
            }
            callback(bounds);
        }
    }

    return addFeature;
}

function buildProposalPopup(attributes) {
    return "<div class='proposal_popup_title'><a href='/proposal/"+attributes.id+"'>"+attributes.title+"</a></div>";
}

function buildInstancePopup(attributes) {
    return "<div class='instance_popup_title'><a href='"+attributes.url+"'>"+attributes.label+"</a></div>";
}


var NUM_ZOOM_LEVELS = 19;

var FALLBACK_BOUNDS = [5.86630964279175, 47.2700958251953, 15.0419321060181, 55.1175498962402];

function loadSingleProposalMap(instanceKey, proposalId, edit, position) {
 $.getScript('/OpenLayers-2.11/build/OpenLayers-closure-img.js', function() {

    var map = createMap(NUM_ZOOM_LEVELS);

    var numFetches = 1;
    if (proposalId) {
       numFethes = 2;
    }
    var waiter = createWaiter(numFetches, function(bounds) {
        map.zoomToExtent(bounds);
    });

    map.addControls(createControls(edit));
    map.addLayers(createBaseLayers());
    map.addLayer(createRegionBoundaryLayer(instanceKey, function(feature) {
        waiter(feature);
    }));

    var proposalLayer = createProposalLayer();
    map.addLayer(proposalLayer);
    map.addControl(createPopupControl(proposalLayer, buildProposalPopup));

    if (edit) {
        var singleProposalFetchedCallback = addEditControls(map, proposalLayer);
    }

    //don't try to fetch proposals geotags when there's no proposal (i.e. if proposal is created)
    if (proposalId) {
        fetchSingleProposal(proposalId, proposalLayer, function(feature) {
            if (edit) {
                singleProposalFetchedCallback(feature);
            }

            waiter(feature);
        });
    } else {
        if (position) {
            var features = new OpenLayers.Format.GeoJSON({}).read(position);
            if (features) {
                var feature = features[0];
                feature.geometry.transform(new OpenLayers.Projection("EPSG:4326"), new OpenLayers.Projection("EPSG:900913"));
                proposalLayer.addFeatures([feature]); 
		singleProposalFetchedCallback(feature);
            } else {
	    	singleProposalFetchedCallback(null);
	    }
        } else {
            singleProposalFetchedCallback(null);
	}
    }
 });
}

function loadRegionMap(instanceKey, initialProposals) {
 $.getScript('/OpenLayers-2.11/build/OpenLayers-closure-img.js', function() {
    var map = createMap(NUM_ZOOM_LEVELS);

    var waiter = createWaiter(1, function(bounds) {
        map.zoomToExtent(bounds);
    });

    map.addControls(createControls(false));
    map.addLayers(createBaseLayers());
    map.addLayer(createRegionBoundaryLayer(instanceKey, function(feature) {
        waiter(feature);
    }));

    var proposalLayer = createRegionProposalsLayer(instanceKey, initialProposals);
    map.addLayer(proposalLayer);
    var popupControl = createPopupControl(proposalLayer, buildProposalPopup);
    map.addControl(popupControl);

    $('.result_list_marker').click(function(event) {
        var target = event.target || event.srcElement;
        var feature = proposalLayer.getFeaturesByAttribute('id', parseInt(target.id.substring('result_list_marker_'.length)))[0];
        popupControl.clickFeature(feature);
    });
 });
}

function loadOverviewMap(initialInstances) {
 $.getScript('/OpenLayers-2.11/build/OpenLayers-closure-img.js', function() {
    var map = createMap(NUM_ZOOM_LEVELS);

    var bounds = new OpenLayers.Bounds.fromArray(FALLBACK_BOUNDS).transform(new OpenLayers.Projection("EPSG:4326"), new OpenLayers.Projection("EPSG:900913"));

    map.addControls(createControls(false));
    map.addLayers(createBaseLayers());

    //var proposalLayer = createRegionProposalsLayer(instanceKey, initialProposals);
    //map.addLayer(proposalLayer);
    //var popupControl = createPopupControl(proposalLayer, buildInstancePopup);
    //map.addControl(popupControl);

    //$('.result_list_marker').click(function(event) {
    //    var target = event.target || event.srcElement;
    //    feature = proposalLayer.getFeaturesByAttribute('id', parseInt(target.id.substring('result_list_marker_'.length)))[0];
    //    popupControl.clickFeature(feature);
    //});

    var overviewLayer = createOverviewLayer();
    map.addLayer(overviewLayer);
    var popupControl = createPopupControl(overviewLayer, buildInstancePopup);
    map.addControl(popupControl);

    map.zoomToExtent(bounds);
    // addMultiBoundaryLayer(map);
 });
}

function noPositionClicked(instanceKey) {
    $('<a>', {
        id: 'create_geo_button', 
        class: 'button_small',
        click: addGeoTagHandler 
    }).append(document.createTextNode("Add geographic location")).appendTo('#map_div');
    $('<a/>').appendTo('#map_div');

    $('#map').remove();
    $('#attribution_div').remove();
    $('#no_geo_button').remove();
    $('#proposal_geotag_field').remove();
    $('#remove_geo_button').remove();
    $('#change_geo_button').remove();
    $('#add_geo_button').remove();
}

function addPositionClicked(instanceKey, position) {

    $('<a>', {
        id: 'no_geo_button', 
        class: 'button_small',
        click: noGeoTagHandler 
    }).append(document.createTextNode("No geographic location")).appendTo('#map_div');
    $('<a/>').appendTo('#map_div');

    $('<div />', {
       id: 'map',
       class: 'edit_map'
    }).appendTo('#map_div');

    loadSingleProposalMap(instanceKey, null, true, position);

    $('#create_geo_button').remove(); 

    $('<div />', { 
        id: 'attribution_div',
        class: 'note_map'
    }).appendTo('#map_div');

    $('#attribution_div').append(document.createTextNode('© '));
    $('<a>', {
        href: 'http://www.openstreetmap.org/'
    }).appendTo('#attribution_div');
    $('#attribution_div').append(document.createTextNode('OpenStreetMap'));
    $('</a>').appendTo('#attribution_div');
    $('#attribution_div').append(document.createTextNode('-KartografInnen('));
    $('<a>', {
        href: 'http://creativecommons.org/licenses/by-sa/2.0/'
    }).appendTo('#attribution_div');
    $('#attribution_div').append(document.createTextNode('lizenz'));
    $('</a>').appendTo('#attribution_div');
    $('#attribution_div').append(document.createTextNode(')'));
    
}

function addGeoTagHandler(event) {
  event.preventDefault(); 
  addPositionClicked($('#instance_key_field').val(), null); 
}

function noGeoTagHandler(event) {
  event.preventDefault();
  noPositionClicked($('#instance_key_field').val());
}

function reloadNewProposalForm() {
     var position = $('#proposal_geotag_field').val(); 
     if (position != null && position != '') {
        addPositionClicked($('#instance_key_field').val(), position);
     }
}

$('#create_geo_button').click(addGeoTagHandler);
$('#create_geo_button').ready(reloadNewProposalForm); 
