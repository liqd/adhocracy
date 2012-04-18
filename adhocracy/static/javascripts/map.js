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

$.ajaxSetup({
  cache: true
});

var popup;

var layersWithPopup = [];

var numberComplexities = 5;

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
    fillOpacity: 0.0,
    strokeColor: "#444444"
};

var styleArea = {
    fillColor: "#66ccff",
    fillOpacity: 0.5,
    strokeColor: "#3399ff"
};

var easteregg = true;
var styleTransparent = {
    fillColor: "#86f286",
    fillOpacity: 0.3,
    strokeOpacity: 0.3
}

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
    });
}


function createOverviewLayers() {

    var layer =  new OpenLayers.Layer.Vector('overview', {
        displayInLayerSwitcher: false,
        projection: new OpenLayers.Projection("EPSG:4326"),
        styleMap: new OpenLayers.StyleMap({'default': new OpenLayers.Style(styleBorder)})
    });

    var url = '/instance/get_instance_regions'; 
    $.ajax({
        url: url,
        success: function(data) {
            var features = new OpenLayers.Format.GeoJSON({}).read(data);
            for (i=0; i<features.length; i++) {
                // assert(features.length==1);
                var feature = features[0];
                feature.geometry.transform(new OpenLayers.Projection("EPSG:4326"), new OpenLayers.Projection("EPSG:900913"));
                layer.addFeatures([feature]);
                //callback(feature);
                if (feature.attributes.admin_center) {
                    var features2 = new OpenLayers.Format.GeoJSON({}).read(feature.attributes.admin_center);
                    var feature2 = features2[0];
                    feature2.geometry.transform(new OpenLayers.Projection("EPSG:4326"), new OpenLayers.Projection("EPSG:900913"));
                    townHallLayer.addFeatures([feature2]);                    
                }
            } 
//            if (features.length == 0) {
//                callback(null);
//            }
        },
        error: function(xhr,err){
            //console.log('No response from server, sorry. url: ' + url + ', Error: '+err);
            //alert('No response from server, sorry. Error: '+err);
        }
    });

    var townHallLayer = new OpenLayers.Layer.Vector('instance_town_hall', {
        displayInLayerSwitcher: false, 
        projection: new OpenLayers.Projection("EPSG:4326"),
        styleMap: new OpenLayers.StyleMap({'default': new OpenLayers.Style(styleProps),
                                           'select': new OpenLayers.Style(styleSelect)})
    });

    return [layer,townHallLayer];

}


function createRegionProposalsLayer(instanceKey, initialProposals, featuresAddedCallback) {

    var rule = new OpenLayers.Rule({
        symbolizer: {
            graphicHeight: 31,
            graphicWidth: 24,
            graphicYOffset: -31
        }
    });

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

    return layer;
}


function createPopupControl(layer, buildPopupContent) {

    layer.events.on({
        'featureselected': function(event) {
            popup = new OpenLayers.Popup.FramedCloud("singlepopup",
                event.feature.geometry.getBounds().getCenterLonLat(),
                null,
                buildPopupContent(event.feature.attributes),
                null,false,null
                );
            this.map.addPopup(popup);
        },
        'featureunselected': function(event) {
            this.map.removePopup(popup);
        }
    });

    layersWithPopup.push(layer);

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

    var townHallLayer = new OpenLayers.Layer.Vector('instance_town_hall', {
        displayInLayerSwitcher: false, 
        projection: new OpenLayers.Projection("EPSG:4326"),
        styleMap: new OpenLayers.StyleMap({'default': new OpenLayers.Style(styleProps),
                                           'select': new OpenLayers.Style(styleSelect)})
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
                if (feature.attributes.admin_center) {
                    var features2 = new OpenLayers.Format.GeoJSON({}).read(feature.attributes.admin_center);
                    var feature2 = features2[0];
                    feature2.geometry.transform(new OpenLayers.Projection("EPSG:4326"), new OpenLayers.Projection("EPSG:900913"));
                    townHallLayer.addFeatures([feature2]);                    
                }
            } else {
                callback(null);
            }
        },
        error: function(xhr,err){
            //console.log('No response from server, sorry. url: ' + url + ', Error: '+err);
            //alert('No response from server, sorry. Error: '+err);
        }
    });

    return [layer,townHallLayer];
}

function createEastereggLayer() {
    var url = '/get_easteregg';
    var layer = new OpenLayers.Layer.Vector('easteregg', {
                    displayInLayerSwitcher: false, 
                    strategies: [new OpenLayers.Strategy.Fixed()],
                    protocol: new OpenLayers.Protocol.HTTP({
                        url: url,
                        params: {
                            year: 2012
                        },
                        format: new OpenLayers.Format.GeoJSON({
                            ignoreExtraDims: true
                        })
                    }),
                    projection: new OpenLayers.Projection("EPSG:4326"),
                    styleMap: new OpenLayers.StyleMap({'default': styleTransparent})
                });

    return layer;
}

function addMultiBoundaryLayer(map) {

    var adminLevels = [2,4,5,6,7,8];
    var layers = new Array();

    //Zoom 0 ... 15 -> 0=hidden,1=visibleByBorder,2=visibleByArea[,3=both (NYI)]
    var displayMap = [
        {styles: [1,0,0,0,0,0]}, //0
        {styles: [1,0,0,0,0,0]}, 
        {styles: [1,0,0,0,0,0]}, 
        {styles: [1,0,0,0,0,0]},
        {styles: [0,1,0,0,0,0]}, //4
        {styles: [0,1,0,0,0,0]},
        {styles: [0,1,0,0,0,0]},
        {styles: [0,1,0,0,0,0]},
        {styles: [0,1,0,1,1,0]}, //8
        {styles: [0,1,0,1,1,0]},
        {styles: [0,0,0,1,1,1]},
        {styles: [0,0,0,1,1,1]},
        {styles: [0,0,0,1,1,1]}, //12
        {styles: [0,0,0,1,1,1]},
        {styles: [0,0,0,1,1,1]},
        {styles: [0,0,0,1,1,1]},
        {styles: [0,0,0,1,1,1]}, //16
        {styles: [0,0,0,1,1,1]},
        {styles: [0,0,0,1,1,1]},
        {styles: [0,0,0,1,1,1]}
    ];
    
    function getLayerIndex(zoomlevel) {
        switch(zoomlevel) {
            case 0: case 1: case 2: case 3: return 0;
            case 4: case 5: case 6: case 7: return 1;
            case 8: case 9: case 10: case 11: return 2;
            case 12: case 13: case 14: case 15: return 3;
            default: case 16: case 17: case 18: case 19: return 4;
        }
    }

    var moveTo = function(bounds, zoomChanged, dragging) {
        var zoom = map.getZoom();
        if (zoomChanged != null) {
            var i=0;
            while (i<adminLevels.length) {
                var styleChanged = displayMap[zoomChanged]['styles'][i];
                var style = displayMap[zoom]['styles'][i];
                var j=0;
                for (j=0; j<numberComplexities; j++) {
                    layers[i][j].setVisibility(false);
                }
                if (styleChanged == 0) {
                    //nop
                } else {
                    layers[i][getLayerIndex(zoomChanged)].setVisibility(true);
                    if (style != styleChanged) {
                        var k=0;
                        if (styleChanged < 2) {
                            for (k=0; k<numberComplexities;k++) {
                                layers[i][k].styleMap['default'] 
                                    = new OpenLayers.Style(styleBorder);
                                layers[i][k].styleMap['default'] 
                                    = new OpenLayers.Style(styleBorder);    
                                redrawFeatures(layers[i][k],styleBorder);
                                redrawFeatures(layers[i][k],styleBorder);
                            }
                        } else {
                            for (k=0; k<numberComplexities;k++) {
                                layers[i][k].styleMap['default'] 
                                    = new OpenLayers.Style(styleArea);    
                                layers[i][k].styleMap['default'] 
                                    = new OpenLayers.Style(styleArea);    
                                redrawFeatures(layers[i][k],styleArea);
                                redrawFeatures(layers[i][k],styleArea);
                            }
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

        layers[layersIdx] = new Array(numberComplexities);
        var complexity;
        for (complexity = 0; complexity < numberComplexities; complexity++) {
            var layername = "layer" + adminLevels[layersIdx] //or aname from config
                + complexity;

            var featureUrl = '/get_boundaries.json';

            layers[layersIdx][complexity] 
                = new OpenLayers.Layer.Vector(layername, {
                    displayInLayerSwitcher: false, 
                    strategies: [new OpenLayers.Strategy.BBOX()],
                    protocol: new OpenLayers.Protocol.HTTP({
                        url: featureUrl,
                        params: {
                            admin_level: adminLevels[layersIdx],
                            complexity: complexity
                        },
                        format: new OpenLayers.Format.GeoJSON({
                            ignoreExtraDims: true
                        })
                    }),
                    projection: new OpenLayers.Projection("EPSG:4326"),
                    styleMap: new OpenLayers.StyleMap({'default':(style < 2 ? new OpenLayers.Style(styleBorder) : new OpenLayers.Style(styleArea))})
                });
            map.addLayer(layers[layersIdx][complexity]);
        }
        layersIdx++;
    }
    map.moveTo = moveTo;

    var townHallLayer = new OpenLayers.Layer.Vector('instance_town_hall', {
        displayInLayerSwitcher: false, 
        projection: new OpenLayers.Projection("EPSG:4326"),
        styleMap: new OpenLayers.StyleMap({'default': new OpenLayers.Style(styleProps),
                                           'select': new OpenLayers.Style(styleSelect)})
    });
    map.addLayer(townHallLayer);
    createPopupControl(townHallLayer, buildInstancePopup);

    foldLayers = foldLayerMatrix(layers);
    for (i=0; i<foldLayers.length;i++) {
        foldLayers[i].events.on({
            'featureadded': function(event) {
               if (event.feature.attributes.admin_center) {
                    var features = new OpenLayers.Format.GeoJSON({}).read(event.feature.attributes.admin_center);
                    var feature = features[0];
                    feature.geometry.transform(new OpenLayers.Projection("EPSG:4326"), new OpenLayers.Projection("EPSG:900913"));
                    townHallLayer.addFeatures([feature]);                    
               }
            }
        })
    }
}

function foldLayerMatrix(layers) {
    var foldLayers = new Array();
    var i=0; var j=0;
    for (i=0; i<layers.length; i++) {
        for (j=0; j<layers[i].length; j++) {
            foldLayers = foldLayers.concat(layers[i][j]);
        }
    }
    return foldLayers;
}

function addRegionSelectControl(map) {

    foldLayers = foldLayerMatrix(layers);

    var selectHoverControl = new OpenLayers.Control.SelectFeature(foldLayers, {
            clickout: false,
            toggle: false,
            multiple: false,
            hover: true,
            highlightOnly: true,
            box: false,
            autoActivate: true,
        });
    map.addControl(selectHoverControl);

    var selectControl = new OpenLayers.Control.SelectFeature(foldLayers, {
            clickout: true,
            toggle: false,
            multiple: false,
            hover: false,
            box: false,
            autoActivate: true,
        });
    map.addControl(selectControl);

    for (i=0; i<foldLayers.length;i++) {
        foldLayers[i].events.on({
            'featureselected': function(event) {
                if (event.feature.attributes.admin_level < 8) {
                    map.zoomToExtent(event.feature.geometry.getBounds());
                }
                if (event.feature.attributes.admin_level == 8) {
                    if (popup) map.removePopup(popup);
                    popup = new OpenLayers.Popup.FramedCloud("singlepopup",
                                                             event.feature.geometry.getBounds().getCenterLonLat(),
                                                             null,
                                                             buildInstancePopup(event.feature.attributes),
                                                             null,false,null
                                                            );
                    map.addPopup(popup);
                }
            },
            'featureunselected': function(event) {
                if (popup) map.removePopup(popup);
            }
        });
    }
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
    //        map.addLayer(new OpenLayers.Layer.Google("Google", {"sphericalMercator": true})); 
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


function createControls(fullControls, keyboardControls) {
    // add map controls

    var mapControls = [
        new OpenLayers.Control.Navigation({'handleRightClicks':true}),
        new OpenLayers.Control.ScaleLine(),
    ];

    if (fullControls) {
        mapControls.push(new OpenLayers.Control.PanZoomBar());
        mapControls.push(new OpenLayers.Control.LayerSwitcher({'ascending':false}));
        // MousePosition currently displays 900913 instead of 4236
        mapControls.push(new OpenLayers.Control.MousePosition());
        mapControls.push(new OpenLayers.Control.Scale());
    }
    if (keyboardControls) {
        // use KeyboardDefault only when map is the central element
        mapControls.push(new OpenLayers.Control.KeyboardDefaults());
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


function buildEastereggPopup(attributes) {
    return "<div class='easteregg_popup_title'><img src='"+attributes.img+"'><br>"+attributes.text+"</div>";
}


function createSelectControl() {

    var selectControl = new OpenLayers.Control.SelectFeature(layersWithPopup, {
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

var NUM_ZOOM_LEVELS = 19;

var FALLBACK_BOUNDS = [5.86630964279175, 47.2700958251953, 15.0419321060181, 55.1175498962402];

function loadSingleProposalMap(openlayers_url, instanceKey, proposalId, edit, position) {
 $.getScript(openlayers_url, function() {

    var map = createMap(NUM_ZOOM_LEVELS);

    var numFetches = 1;
    if (proposalId) {
       numFetches = 2;
    }
    var waiter = createWaiter(numFetches, function(bounds) {
        map.zoomToExtent(bounds);
    });

    map.addControls(createControls(edit, false));
    map.addLayers(createBaseLayers());
    var regionBoundaryLayers = createRegionBoundaryLayer(instanceKey, function(feature) {
                                    waiter(feature);
                                });
    map.addLayers(regionBoundaryLayers);
    createPopupControl(regionBoundaryLayers[1], buildInstancePopup);

    var proposalLayer = createProposalLayer();
    map.addLayer(proposalLayer);
    createPopupControl(proposalLayer, buildProposalPopup);

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
        var feature = null;
        if (position) {
            var features = new OpenLayers.Format.GeoJSON({}).read(position);
            if (features) {
                feature = features[0];
                feature.geometry.transform(new OpenLayers.Projection("EPSG:4326"), new OpenLayers.Projection("EPSG:900913"));
                proposalLayer.addFeatures([feature]); 
        }
    }
        singleProposalFetchedCallback(feature);
    }
    if (easteregg) {
        var easterLayer = createEastereggLayer();
        map.addLayer(easterLayer);
        createPopupControl(easterLayer, buildEastereggPopup);
    }
    map.addControl(createSelectControl());
 });
}

function loadRegionMap(openlayers_url, instanceKey, initialProposals) {
 $.getScript(openlayers_url, function() {
    var map = createMap(NUM_ZOOM_LEVELS);

    var waiter = createWaiter(1, function(bounds) {
        map.zoomToExtent(bounds);
    });

    map.addControls(createControls(false, false));
    map.addLayers(createBaseLayers());
    var regionBoundaryLayers = createRegionBoundaryLayer(instanceKey, function(feature) {
        waiter(feature);
    });
    map.addLayers(regionBoundaryLayers);
    createPopupControl(regionBoundaryLayers[1], buildInstancePopup);

    var proposalLayer = createRegionProposalsLayer(instanceKey, initialProposals);
    map.addLayer(proposalLayer);
    var popupControl = createPopupControl(proposalLayer, buildProposalPopup);

    if (easteregg) {
        var easterLayer = createEastereggLayer();
        map.addLayer(easterLayer);
        createPopupControl(easterLayer, buildEastereggPopup);
    }
    var selectControl = createSelectControl();

    $('.result_list_marker').click(function(event) {
        var target = event.target || event.srcElement;
        var feature = proposalLayer.getFeaturesByAttribute('id', parseInt(target.id.substring('result_list_marker_'.length)))[0];
        selectControl.clickFeature(feature);
    });
    map.addControl(selectControl);
 });
}

function loadOverviewMap(openlayers_url, initialInstances) {
 $.getScript(openlayers_url, function() {
    var map = createMap(NUM_ZOOM_LEVELS);

    var bounds = new OpenLayers.Bounds.fromArray(FALLBACK_BOUNDS).transform(new OpenLayers.Projection("EPSG:4326"), new OpenLayers.Projection("EPSG:900913"));

    map.addControls(createControls(false, false));
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

    var overviewLayers = createOverviewLayers();
    map.addLayers(overviewLayers);
    createPopupControl(overviewLayers[1], buildInstancePopup);

    if (easteregg) {
        var easterLayer = createEastereggLayer();
        map.addLayer(easterLayer);
        createPopupControl(easterLayer, buildEastereggPopup);
    }

    map.zoomToExtent(bounds);
    // addMultiBoundaryLayer(map);
    
    map.addControl(createSelectControl());

 });
}

function loadSelectInstanceMap(openlayers_url) {
  $.getScript(openlayers_url, function() {
    var map = createMap(NUM_ZOOM_LEVELS);

    var bounds = new OpenLayers.Bounds.fromArray(FALLBACK_BOUNDS).transform(new OpenLayers.Projection("EPSG:4326"), new OpenLayers.Projection("EPSG:900913"));

    map.addControls(createControls(true, false));
    map.addLayers(createBaseLayers());

    addMultiBoundaryLayer(map);

    map.zoomToExtent(bounds);
    
    map.addControl(createSelectControl());
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

    $('#attribution_div').append(document.createTextNode('&copy; '));
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

function instanceSearch(openlayers_url) {
  $.getScript(openlayers_url, function() {

    var resultList = new Array();
    var max_rows = 5;
    var offset = 0;

    function makeRegionNameElements(item) {
        if (item.id != "") {
            return $('<a>', {
               class: "link",
               href: item.url 
            }).append(document.createTextNode(item.label));
        } else {
            return document.createTextNode( item.label );
        }
    }

    function makeRegionDetailsElements(item) {
        if (item.id != "") {
            return document.createTextNode(item.num_proposals + ' proposals \u00B7 '
                                                 + item.num_papers + ' papers \u00B7 '
                                                 + item.num_members + ' members \u00B7 '
                                                 + 'creation date: ' + item.create_date);
        }
    }

    function instanceEntry( item ) {
        var li = $('<li>',{ class: "content_box" });
        var marker = $('<div>', { class: "marker" });
        var h4 = $('<h4>');
        var text;
        var details;

        text = makeRegionNameElements(item);
        details = makeRegionDetailsElements(item);
    
        li.append(marker);
        li.append(h4);
        h4.append(text);
        if (item.id != "") {
            li.append(details);
        }
        li.appendTo('#log');

        $( "#log" ).scrollTop( 0 );
    }

    function resetSearchField(inputValue, count) {
        $('#log').empty();
        $('#search_buttons').empty()
        $('#num_search_result').empty();
        var resultText = document.createTextNode('Your search for \"' + inputValue + '\" results in ' + count + ' hits.');
        $('#num_search_result').append(resultText);
    }

    function fillSearchField(inputValue) {
        //insert result into list
        var count = resultList[inputValue].length;
        resetSearchField(inputValue, count);

        for (var i = offset; i < offset+max_rows && i < count; ++i) {
            instanceEntry(resultList[inputValue][i]);
        }
        if(count > max_rows) {
            if (offset + max_rows > max_rows) {
                var prevButton = $( '<div />', { class: 'button_small', id: 'search_prev' });
                var prevText = document.createTextNode('prev');
                prevButton.append(prevText);
                prevButton.appendTo('#search_buttons');
                prevButton.click(function(event) { offset = offset-max_rows; fillSearchField(inputValue) });
            }
            var pageText = document.createTextNode(offset + ' to ' + (offset+max_rows));
            $('#search_buttons').append(pageText);
            if (offset + max_rows < count) {
                var nextButton = $( '<div />', { class: 'button_small', id: 'search_next' });
                var nextText = document.createTextNode('next');
                nextButton.append(nextText);
                nextButton.appendTo('#search_buttons');
                nextButton.click(function(event) { offset = offset+max_rows; fillSearchField(inputValue) });
            }
        } else {
            $('#search_next').remove();
            $('#search_prev').remove();
        }
    }

    function showSearchResult() {
        var inputValue = $( "#instances" ).val();
        $( "#instances" ).autocomplete("close");
        if (resultList[inputValue]) {
            fillSearchField(inputValue);
        }
    }

    $( "#instances" ).keypress(function(event) {
        if ( event.which == 13 || event.which == 10) {
            showSearchResult();
        }
    });

    $('#search_button').click(showSearchResult);

//    var offset = $('#search_offset_field').val();
//    if (offset == "") {
//        offset = 0;
//    }

    $( "#instances" ).autocomplete({
        source: function( request, response ) {
        $.ajax({
            url: "/find_instances.json",
            dataType: "jsonp",
            data: {
//                max_rows: 5,
//                offset: offset,
                name_contains: request.term
            },
            success: function( data ) {
                resultList[request.term] = $.map( data.search_result, function( item ) {
//                    var admin_center;
//                    var features = new OpenLayers.Format.GeoJSON({}).read(item.admin_center);
//                    if (features != null && features.length > 0) {
//                        admin_center = OpenLayers.Projection.transform(features[0].geometry,new OpenLayers.Projection("EPSG:4326"), new OpenLayers.Projection("EPSG:900913"));
//                    }
                    return {
                        id: item.id,
                        label: item.name,
                        url: item.url,
                        value: item.name,
                        num_proposals: item.num_proposals,
                        num_papers: item.num_papers,
                        num_members: item.num_members,
                        create_date: item.create_date,
//                        admin_center: admin_center
                    }
                })
                //fill into autocompletion drop down
                response( resultList[request.term] );
            }
        });
    },
    minLength: 2,
    select: function(event, ui) { if (ui.item) {
                                    if (ui.item.url) { 
                                        //window.location.replace(ui.item.url);
                                        $(location).attr('href',ui.item.url);
                                    } else {
                                        resetSearchField(ui.item.label, 1);
                                        instanceEntry(ui.item);
                                    }
                                  }
                                },
    open: function() {
        $( this ).removeClass( "ui-corner-all" ).addClass( "ui-corner-top" );
    },
    close: function() {
       $( "#instances" ).removeClass( "ui-corner-top" ).addClass( "ui-corner-all" );
    }
  });
 });
}
