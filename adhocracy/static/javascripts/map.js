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

 */

$.ajaxSetup({
  cache: true
});


/* default map configuration */

var RESOLUTIONS = [
    // 156543.03390625, 78271.516953125, 39135.7584765625, 19567.87923828125, 9783.939619140625,
    4891.9698095703125, 2445.9849047851562, 1222.9924523925781, 611.4962261962891, 305.74811309814453, 152.87405654907226, 76.43702827453613, 38.218514137268066, 19.109257068634033, 9.554628534317017, 4.777314267158508, 2.388657133579254, 1.194328566789627, 0.5971642833948135
    // 0.29858214169740677, 0.14929107084870338, 0.07464553542435169
    ]
var NUM_ZOOM_LEVELS = RESOLUTIONS.length;
var FALLBACK_BOUNDS = [5.86630964279175, 47.2700958251953, 15.0419321060181, 55.1175498962402];

var popup;

var layersWithPopup = [];

var numberComplexities = 5;

var inputValue = new String();
var prevInputValue = new String();

var styleProps = {
    pointRadius: 5,
    fillColor: "#f28686",
    fillOpacity: 0.8,
    strokeColor: "#be413f",
    strokeWidth: 1,
    strokeOpacity: 0.8
};

var styleTransparentProps = {
    pointRadius: 5,
    fillColor: "#ffffff",
    fillOpacity: 0.0,
    strokeColor: "#ffffff",
    strokeWidth: 1,
    strokeOpacity: 0.0
}

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

var easteregg = false;
var styleEasteregg = {
    fillColor: "#86f286",
    fillOpacity: 0.3,
    strokeOpacity: 0.3
}


/* projections */

var geographic;
var mercator;


function createProposalLayer() {

    return new OpenLayers.Layer.Vector("proposal", {
        displayInLayerSwitcher: false, 
        projection: mercator,
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
//                feature.geometry.transform(geographic, mercator);
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
        projection: mercator,
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
//                feature.geometry.transform(geographic, mercator);
                layer.addFeatures([feature]);
                //callback(feature);
                if (feature.attributes.admin_center) {
                    var features2 = new OpenLayers.Format.GeoJSON({}).read(feature.attributes.admin_center);
                    var feature2 = features2[0];
//                    feature2.geometry.transform(geographic, mercator);
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
        projection: mercator,
        styleMap: new OpenLayers.StyleMap({'default': new OpenLayers.Style(styleProps),
                                           'select': new OpenLayers.Style(styleSelect)})
    });

    return [layer,townHallLayer];

}

function makeFilterRule() {
return new OpenLayers.Rule({
        symbolizer: {
            graphicHeight: 31,
            graphicWidth: 24,
            graphicYOffset: -31
        }
    });
}

function createRegionProposalsLayer(instanceKey, initialProposals, featuresAddedCallback) {

    var rule = makeFilterRule(); 
    rule.evaluate = function (feature) {
        if (initialProposals) {
            var index = initialProposals.indexOf(feature.fid);

            if (index >= 0) {
                if (index < 10) {
                    var letter = String.fromCharCode(index+97);
                    this.symbolizer.externalGraphic = '/images/map_marker_pink_'+letter+'.png';
                    $('#result_list_marker_'+feature.fid).attr('alt', letter).addClass('marker_'+letter);
                    return true;
                } else {
                    $('#result_list_marker_'+feature.fid).attr('alt', index).addClass('bullet_marker');
                    return false;
                }
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
        projection: mercator,
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

    function openPopup(event) {
        popup = new OpenLayers.Popup.FramedCloud("singlepopup",
                        event.feature.geometry.getBounds().getCenterLonLat(),
                        null,
                        buildPopupContent(event.feature.attributes),
                        null,false,null
                        );
        this.map.addPopup(popup);
    }

    function closePopup(event) {
        if (popup) {
            this.map.removePopup(popup);
            popup = null;
        }
    }

    layer.events.on({
        'featureselected': openPopup,
        'featureunselected': closePopup
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
            text: LANG.set_position_text
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
            text: LANG.set_different_position_text
        }).appendTo('#edit_map_buttons');

        $('<a />', {
            id: 'remove_geo_button',
            class: 'button',
            click: function() {
                layer.removeAllFeatures();
                $('#proposal_geotag_field').val('');
                updateEditButtons();
            },
            text: LANG.remove_position_text 
        }).appendTo('#edit_map_buttons');
    }

    function updateGeotagField() {
        var transformed_feature = layer.features[0].clone();
//        transformed_feature.geometry.transform(mercator, geographic);
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
        projection: mercator,
        styleMap: new OpenLayers.StyleMap({'default': new OpenLayers.Style(styleBorder)}),
    })

    var townHallLayer = new OpenLayers.Layer.Vector('instance_town_hall', {
        displayInLayerSwitcher: false, 
        projection: mercator,
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
//                feature.geometry.transform(geographic, mercator);
                layer.addFeatures([feature]);
                callback(feature);
                if (feature.attributes.admin_center) {
                    var features2 = new OpenLayers.Format.GeoJSON({}).read(feature.attributes.admin_center);
                    var feature2 = features2[0];
//                    feature2.geometry.transform(geographic, mercator);
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
                    projection: mercator,
                    styleMap: new OpenLayers.StyleMap({'default': styleEasteregg})
                });

    return layer;
}

function layerHasFeature(layer, feature) {
    var i=0;
    for (i=0; i<layer.features.length; i++) {
        if (layer.features[i].attributes.region_id == feature.attributes.region_id) {
           return true;
        }
    }
    return false;
}

function listHasFeature(list, feature) {
    var i=0;
    for (i=0; i<list.length; i++) {
        if (list[i].region_id == feature.attributes.region_id) {
            return true;
        }
    }
    return false;
}

function addMultiBoundaryLayer(map, layers, tiles, townHallTiles, resultList) {

    var adminLevels = [4,5,6,7,8];
    var townHallTiles = new Array(adminLevels.length);
    var i=0;
    for (i=0;i<adminLevels.length;i++) {
        townHallTiles[i] = new Array();
    }

    //Zoom 0 ... 19 -> 0=hidden,1=borderColor1,2=borderColor2,3=borderColor3,...]
    var displayMap = [
        {styles: [1,0,0,0,0]},
        {styles: [1,0,0,0,0]},
        {styles: [1,0,0,0,0]},
        {styles: [1,0,1,0,0]},
        {styles: [1,0,1,0,0]}, //4
        {styles: [0,0,1,1,0]},
        {styles: [0,0,1,1,0]},
        {styles: [0,0,1,1,1]},
        {styles: [0,0,1,1,1]}, //8
        {styles: [0,0,1,1,1]},
        {styles: [0,0,1,1,1]},
        {styles: [0,0,1,1,1]},
        {styles: [0,0,1,1,1]}, //12
        {styles: [0,0,1,1,1]},
        {styles: [0,0,1,1,1]}
    ];
    
    function makeTiles(sizeLL, bounds) {
        var xStart = Math.floor(bounds.left / sizeLL);
        var yStart = Math.floor(bounds.bottom / sizeLL);
        var tiles = new Array();
        var x = xStart;
        do {
             var y = yStart;
             do {
                  tiles.push({x: x, y: y});
                  y += 1;
             } while ((y * sizeLL) < bounds.top);
             x += 1;
        } while ((x * sizeLL) < bounds.right);
        return tiles;
    }
    
    function alreadyFetched(tiles, tile) {
        var fetch = true;
        var i=0;
        for (i=0; i<tiles.length; i++) {
            if (tile.x == tiles[i].x
                && tile.y == tiles[i].y) {
                    fetch = false;
            }
        }
        return !fetch;
    }

    function showTownHall(visible, admin_level) {
        for (k=0; k<townHallLayer.features.length; k++) {
            var feature = townHallLayer.features[k];
            var style = styleProps;
            //features in search result are always visible
            if (!visible || (!resultList || !resultList[inputValue] || !listHasFeature(resultList[inputValue],feature))) {
                style = styleTransparentProps;
            }
            if (feature.attributes.admin_level == admin_level) {
                feature.style = new OpenLayers.Style(style);
                townHallLayer.drawFeature(feature,style);
            }
        }
    }

    var moveTownHallTo 
        = function(bounds, zoomChanged, dragging ) {
            var zoom = map.getZoom();
            var i=0;
            while (i<adminLevels.length) {
                var style = displayMap[zoom]['styles'][i];
                if (style == 0) {
                    //make townHalls invisible
                    showTownHall(false, adminLevels[i]);
                } else if (style == 1 || style == 2) {
                    //fetch townHalls
                    var tileSize = 256;
                    var tileSizeLL = tileSize * map.getResolution();
                    var newTiles = makeTiles(tileSizeLL, bounds);
                    var j=0;
                    for (j=0; j < newTiles.length; j++) {
                        var fetch = !alreadyFetched(townHallTiles[i], newTiles[j]);
                        if (fetch) {
                            townHallTiles[i].push(newTiles[j]);
                            //box = new OpenLayers.Bounds(newTiles[j].x*tileSizeLL,newTiles[j].y*tileSizeLL,
                            //                            (newTiles[j].x+1)*tileSizeLL,(newTiles[j].y+1)*tileSizeLL);
                            //townHallLayer.addFeatures([new OpenLayers.Feature.Vector(box.toGeometry(),{})]);

                            var url = '/get_admin_centers.json'
                                                    + '?x=' + newTiles[j].x
                                                    + '&y=' + newTiles[j].y
                                                    + '&tileSize=' + tileSize
                                                    + '&res=' + map.getResolution()
                                                    + '&admin_level=' + adminLevels[i];
                            $.ajax({
                                url: url,
                                success: function(data) {
                                    var features = new OpenLayers.Format.GeoJSON({}).read(data);
                                    var k=0;
                                    for (k=0; k<features.length; k++) {
                                        var feature = features[k];
                                        if (feature.geometry !== null) {
                                            townHallLayer.addFeatures([feature]);
                                        }
                                    }
                                    showTownHall(true, adminLevels[i]);
                                },
                                error: function(xhr,err) {
                                    // console.log("error: " + err);
                                }
                            });
                        }
                    }
                    //make townHalls visible
                    showTownHall(true, adminLevels[i]);
                }
                i++;
            }
        }

    var moveMapTo = function(bounds, zoomChanged, dragging) {
        var zoom = map.getZoom();
        if (zoom != null && zoomChanged != null) {
            var i=0;k=0;
            while (i<adminLevels.length) {
                var styleChanged = displayMap[zoomChanged]['styles'][i];
                var style = displayMap[zoom]['styles'][i];
                var j=0;
                for (j=0; j<displayMap.length; j++) {
                    layers[i][j].setVisibility(false);
                }
                if (styleChanged == 0) {
                    //nop
                } else {
                    layers[i][zoomChanged].setVisibility(true);
                    if (style != styleChanged) {
                        var k=0;
                        if (styleChanged < 2) {
                            for (k=0; k<displayMap.length;k++) {
                                layers[i][k].styleMap['default'] 
                                    = new OpenLayers.Style(styleBorder);
                                layers[i][k].styleMap['default'] 
                                    = new OpenLayers.Style(styleBorder);    
                                redrawFeatures(layers[i][k],styleBorder);
                            }
                        } else {
                            for (k=0; k<displayMap.length;k++) {
                                layers[i][k].styleMap['default'] 
                                    = new OpenLayers.Style(styleArea);    
                                layers[i][k].styleMap['default'] 
                                    = new OpenLayers.Style(styleArea);    
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

    function addBoundaryPaths(zoom, data) {
        var features = new OpenLayers.Format.GeoJSON({}).read(data);
        if (features) {
            var k=0;
            for (k=0; k<features.length; k++) {
                var feature = features[k];
                if (feature.geometry !== null) {
                    var admin_level = parseInt(feature.attributes.admin_level);
                    var zoom = parseInt(feature.attributes.zoom);
                    if (zoom >= 0 && zoom < 15 && isValidAdminLevel(admin_level)) {
                        layers[getLayerIndex(admin_level)][zoom].addFeatures([feature]);
                    }
                }
            }
        }
    }
  
    var moveLayersTo
        = function(bounds, zoomChanged, dragging ) {
              if (this.getVisibility()) {
                  var tileSize = 256;
                  var tileSizeLL = tileSize * map.getResolution();
                  var newTiles = makeTiles(tileSizeLL, bounds);
                  var i=0;
                  for (i=0; i < newTiles.length; i++) {
                      var fetch = !alreadyFetched(tiles[this.layersIdx], newTiles[i]);
                      if (fetch) {
                          tiles[this.layersIdx].push(newTiles[i]);
                          box = new OpenLayers.Bounds(newTiles[i].x*tileSizeLL,newTiles[i].y*tileSizeLL,
                                                      (newTiles[i].x+1)*tileSizeLL,(newTiles[i].y+1)*tileSizeLL);
                          layers[this.layersIdx][this.zoom].addFeatures([new OpenLayers.Feature.Vector(box.toGeometry(),
                                                                                                              {})]);
                                  //transform bbox with shapely
                          var url = '/get_tiled_boundaries.json'
                                          + '?x=' + newTiles[i].x
                                          + '&y=' + newTiles[i].y
                                          + '&zoom=' + this.zoom
                                          + '&admin_level=' + adminLevels[this.layersIdx];
                          $.ajax({
                              url: url,
                              success: function(data) {addBoundaryPaths(this.zoom, data);},
                              error: function(xhr,err) {
                                  // console.log("error: " + err);
                              }
                          });
                      }
                  }
              }
              OpenLayers.Layer.Vector.prototype.moveTo.apply(this, arguments);
            }

    function redrawFeatures(thelayer,thestyle) {
        var i=0;
        for (i=0; i<thelayer.features.length;i++) {
            thelayer.features[i].style = thestyle;
            thelayer.drawFeature(thelayer.features[i],thestyle);
        } 
    }

    function isValidAdminLevel(admin_level) {
        var i=0;
        for (i=0; i<adminLevels.length; i++) {
            if (adminLevels[i] == admin_level) {
                return true;
            }
        }
        return false;
    }

    function getLayerIndex(admin_level) {
        return adminLevels.indexOf(admin_level);
    }

    var layersIdx = 0;
    while (layersIdx < adminLevels.length) {
        var style = displayMap[map.getZoom()]['styles'][layersIdx];

        layers[layersIdx] = new Array(displayMap.length);
        tiles[layersIdx] = new Array();
        var z;
        for (z=0; z < displayMap.length; z++) {
            var layername = "layer" + adminLevels[layersIdx] + z;

            layers[layersIdx][z] 
                = new OpenLayers.Layer.Vector(layername, {
                    displayInLayerSwitcher: false, 
                    projection: mercator,
                    styleMap: new OpenLayers.StyleMap({'default':(style < 2 ? new OpenLayers.Style(styleBorder) : new OpenLayers.Style(styleArea))}),
                    layersIdx: layersIdx,
                    zoom: z
                });
                layers[layersIdx][z].moveTo = moveLayersTo; 
            map.addLayer(layers[layersIdx][z]);
        }
        layersIdx++;
    }
    map.moveTo = moveMapTo;

    var rule = makeFilterRule(); 
    rule.evaluate = function (feature) {
        if (resultList) {
            if (resultList[inputValue]) {
                var result = resultList[inputValue];
                var i=0;
                var numInstance = 0;
                for (i=0; i<result.length; i++) {
                    if (result[i].region_id == feature.attributes.region_id
                        && result[i].instance_id != "") {
                        var letter = String.fromCharCode(numInstance+97);
                        this.symbolizer.externalGraphic = '/images/map_marker_pink_'+letter+'.png';
                        return true;
                    }
                    if (result[i].instance_id != "") numInstance = numInstance + 1;
                }
            }
            return false;
        } else {
            return false;
        }
    }

    var townHallLayer = new OpenLayers.Layer.Vector('instance_town_hall', {
        displayInLayerSwitcher: false, 
        projection: mercator,
        styleMap: new OpenLayers.StyleMap({
            'default': new OpenLayers.Style(styleProps, {rules: [
                rule,
                new OpenLayers.Rule({elseFilter: true})
            ]}),
            'select': new OpenLayers.Style(styleSelect)
        }),
    });
    townHallLayer.moveTo = moveTownHallTo; 
    map.addLayer(townHallLayer);
    createPopupControl(townHallLayer, buildInstancePopup);

    var foldLayers = foldLayerMatrix(layers);
    return [townHallLayer,foldLayers];
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

    var foldLayers = foldLayerMatrix(layers);

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
                if (popup) { 
                    map.removePopup(popup);
                    popup = null;
                }
            }
        });
    }
}


function createBaseLayers(blank) {

    // workaround allowing to limit zoom levels
    // http://lists.osgeo.org/pipermail/openlayers-users//2012-January/023746.html
    
    var osmOptions = {
        isBaseLayer:true,
        displayInLayerSwitcher:true,
        zoomOffset:5,
        resolutions: RESOLUTIONS
    };

    var baseLayers = [
        //default Openstreetmap Baselayer
        new OpenLayers.Layer.OSM("Open Street Map", "", osmOptions),
        new OpenLayers.Layer.OSM("Public Transport",
                    "http://a.tile2.opencyclemap.org/transport/${z}/${x}/${y}.png", osmOptions),
        new OpenLayers.Layer.OSM("Transport Map",
                    "http://otile1.mqcdn.com/tiles/1.0.0./osm/${z}/${x}/${y}.png", osmOptions),
        new OpenLayers.Layer.OSM("&Ouml;pnv Deutschland", 
                    "http://tile.xn--pnvkarte-m4a.de/tilegen/${z}/${x}/${y}.png", osmOptions)
            ];

    // Blank Baselayer
    if (blank) {
        baseLayers.push(new OpenLayers.Layer("Blank",{isBaseLayer: true}));
    }

    return baseLayers;
}


function createMap() {

    geographic = new OpenLayers.Projection("EPSG:4326");
    mercator = new OpenLayers.Projection("EPSG:900913");

    RESTRICTED_BOUNDS = new OpenLayers.Bounds(0, 40, 30, 60)

    return new OpenLayers.Map('map', {
        // maxExtent: new OpenLayers.Bounds(-180, -90, 180, 90),
        restrictedExtent: RESTRICTED_BOUNDS.transform(geographic, mercator),
        // maxResolution: 156543.0399,
        numZoomLevels: NUM_ZOOM_LEVELS,
        units: 'm',
        projection: mercator,
        //displayProjection: geographic,
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
        // mapControls.push(new OpenLayers.Control.MousePosition());
        mapControls.push(new OpenLayers.Control.Scale());
        // mapControls.push(new OpenLayers.Control.Graticule());
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
                bounds = new OpenLayers.Bounds.fromArray(FALLBACK_BOUNDS).transform(geographic, mercator);
            }
            callback(bounds);
        }
    }

    return addFeature;
}

function buildProposalPopup(attributes) {
    return "<div class='proposal_popup_title'><a href='/proposal/"+attributes.region_id+"'>"+attributes.title+"</a></div>";
}

function buildInstancePopup(attributes) {
    var result = "<div class='instance_popup_title'>";
    if (attributes.url) {
        result = result + "<a href='"+attributes.url+"'>";
    }
    var label = attributes.label;
    if (attributes.admin_type) {
        label += " (" + attributes.admin_type + ")"
    }
    result = result + label+"</a></div>";
    return result;
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

//var FALLBACK_BOUNDS = [10, 51, 10.1, 51.1];

function loadSingleProposalMap(openlayers_url, instanceKey, proposalId, edit, position) {
 $.getScript(openlayers_url, function() {

    var map = createMap();

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
//                feature.geometry.transform(geographic, mercator);
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

function enableMarker(id, layer, selectControl) {
    $('.'+id).click(function(event) {
        var target = event.target || event.srcElement;
        var feature = layer.getFeaturesByAttribute('region_id', parseInt(target.id.substring((id+'_').length)))[0];
        if (popup) {
            var flonlat = feature.geometry.getBounds().getCenterLonLat();
            var plonlat = popup.lonlat;
            selectControl.clickoutFeature(feature);
            if (plonlat != flonlat) {
                selectControl.clickFeature(feature);
            }
        } else {
            selectControl.clickFeature(feature);
        }
    });
}

function loadRegionMap(openlayers_url, instanceKey, initialProposals) {
 $.getScript(openlayers_url, function() {
    var map = createMap();

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
    enableMarker('result_list_marker', proposalLayer, selectControl);
    map.addControl(selectControl);
 });
}

function loadOverviewMap(openlayers_url, initialInstances) {
 $.getScript(openlayers_url, function() {
    var map = createMap();

    var bounds = new OpenLayers.Bounds.fromArray(FALLBACK_BOUNDS).transform(geographic, mercator);

    map.addControls(createControls(false, false));
    map.addLayers(createBaseLayers());

    //var proposalLayer = createRegionProposalsLayer(instanceKey, initialProposals);
    //map.addLayer(proposalLayer);
    //var popupControl = createPopupControl(proposalLayer, buildInstancePopup);
    //map.addControl(popupControl);

    //enableMarker('result_list_marker', proposalLayer, popupControl);

    var overviewLayers = createOverviewLayers();
    map.addLayers(overviewLayers);
    createPopupControl(overviewLayers[1], buildInstancePopup);

    if (easteregg) {
        var easterLayer = createEastereggLayer();
        map.addLayer(easterLayer);
        createPopupControl(easterLayer, buildEastereggPopup);
    }

    map.zoomToExtent(bounds);
    
    map.addControl(createSelectControl());

 });
}

function loadSelectInstance(openlayers_url) {
  $.getScript(openlayers_url, function() {
    var layers = new Array();
    var tiles = new Array();
    var resultList = new Array();
    var state = loadSelectInstanceMap(layers, tiles, resultList);
    instanceSearch(state, resultList);
  });
}

function loadSelectInstanceMap(layers, tiles, resultList) {

    function addArrow(plus) {
        var src = '/images/map_resize_rec_plus.png';
        if (!plus) {
            src = '/images/map_resize_rec_minus.png';
        }
        var img = $('<img>', { src: src,
                               alt: '+'
                             });
        $('.arrow').empty();
        $('.arrow').append(img);
    }

    function enlargeMap(event) {
       addArrow(false); 
       $('.arrow').click(shrankMap);
       $('#map_startpage_wrapper').removeClass('map_size_normal');
       $('#map_startpage_wrapper').addClass('map_size_large');
       map.updateSize();
    }

    function shrankMap(event) {
       addArrow(true);
       $('.arrow').click(enlargeMap);
       $('#map_startpage_wrapper').addClass('map_size_normal');
       $('#map_startpage_wrapper').removeClass('map_size_large');
       map.updateSize();
    }

    var map = createMap();
    var bounds = new OpenLayers.Bounds.fromArray(FALLBACK_BOUNDS).transform(geographic, mercator);

    map.addControls(createControls(true, false));
    map.addLayers(createBaseLayers());

    var layers2 = addMultiBoundaryLayer(map, layers, tiles, resultList);
    var townHallLayer = layers2[0];
    var foldLayers = layers2[1];
 
    var selectControl = createSelectControl();
    map.addControl(selectControl);

    map.zoomToExtent(bounds);
  
    addArrow(true);
    $('.arrow').click(enlargeMap);

    var result = {map: map, 
                  foldLayers: foldLayers,
                  townHallLayer: townHallLayer, 
                  selectControl: selectControl};

    return result;
}

function instanceSearch(state, resultList) {

    var map = state.map;
//    var foldLayers = state.foldLayers;
    var townHallLayer = state.townHallLayer;
    var selectControl = state.selectControl;

    var max_rows = 3;
    var offset = 0;

    $('#instances').click(function(event) { $('#instances').val('');
                                            $('#instances').unbind('click'); });

    function makeRegionNameElements(item) {
        var text = item.label;
        var text2 = "";
        var is_in = item.is_in;
        while (is_in !== undefined) {
            text2 = is_in.name;
            is_in = is_in.is_in;
        };
        if (text2 != "") {
            text = text + ", " + text2;
        }
        if (item.instance_id != "") {
            return $('<a>', {
               class: "link",
               href: item.url 
            }).append(document.createTextNode(text));
        } else {
            return document.createTextNode(text);
        }
    }

    function makeRegionDetailsElements(item) {
        if (item.instance_id != "") {
            return document.createTextNode(
                item.num_proposals + ' '
                + LANG.proposals_text +' \u00B7 '
                + item.num_papers + ' '
                + LANG.papers_text +' \u00B7 '
                + item.num_members + ' '
                + LANG.members_text + ' \u00B7 '
                + LANG.creation_date_text + ' ' 
                + item.create_date);
        }
    }

    function instanceEntry( item, num ) {
        var idBase = 'search_result_list_marker'
        var letter = String.fromCharCode(num + 97);
        var li = $('<li>',{ class: 'content_box' });
        var marker;
        var img;
        if (item.instance_id != "") {
            marker = $('<div>', { class: 'marker' });
            img = $('<img>', { class: 'search_result_list_marker marker_' + letter,
                               src: '/images/map_marker_pink_'+letter+'.png',
                               id: idBase + '_' + item.region_id,
                               alt: item.region_id
                             });
        } else {
            marker = $('<div>', { class: 'bullet_marker' });
            img = $('<img>', { class: 'search_result_list_marker bullet_marker',
                               src: '/images/bullet.png',
                               id: idBase + '_' + item.region_id,
                               alt: item.region_id
                             });
        }
        var h4 = $('<h4>');
        var text;
        var details;

        text = makeRegionNameElements(item);
        details = makeRegionDetailsElements(item);

        marker.append(img);
        li.append(marker);
        li.append(h4);
        h4.append(text);
        if (item.instance_id != "") {
            li.append(details);
        }
        li.appendTo('#log');

        $( "#log" ).scrollTop( 0 );
    }

    function resetSearchField(inputValue, count) {
        $('#log').empty();
        $('#search_buttons').empty()
        $('#num_search_result').empty();
        var text = LANG.num_search_result_start_text 
                    + ' \"' + inputValue + '\" '
                    + LANG.num_search_result_end_text 
                    + ' ' + count + ' ';
        if (count == 1) text = text + LANG.hit_text;
        else text = text + LANG.hits_text;
        text = text + '.';
        var resultText = document.createTextNode(text);
        $('#num_search_result').append(resultText);
    }

    function fillSearchField(inputValue) {
        //insert result into list
        var count = resultList[inputValue].length;
        resetSearchField(inputValue, count);
        addMarkers(inputValue);

        var numInstance = 0;
        for (var i = offset; i < offset+max_rows && i < count; ++i) {
            instanceEntry(resultList[inputValue][i], numInstance);
            if (resultList[inputValue][i].instance_id != "") {
                numInstance = numInstance + 1;
            }
        }
        enableMarker('search_result_list_marker', townHallLayer, selectControl); 
        
        if(count > max_rows) {
            if (offset + max_rows > max_rows) {
                var prevButton = $( '<div />', { class: 'button_small', id: 'search_prev' });
                var prevText = document.createTextNode(LANG.prev_text);
                prevButton.append(prevText);
                prevButton.appendTo('#search_buttons');
                prevButton.click(function(event) { removePreviousMarkers(inputValue); offset = offset-max_rows; fillSearchField(inputValue) });
            }
            var lastPage = Math.min(offset+max_rows,count);
            var pageText = document.createTextNode((offset+1) + ' '
                            + LANG.to_text + ' ' + lastPage);
            $('#search_buttons').append(pageText);
            if (offset + max_rows < count) {
                var nextButton = $( '<div />', { class: 'button_small', id: 'search_next' });
                var nextText = document.createTextNode(LANG.next_text);
                nextButton.append(nextText);
                nextButton.appendTo('#search_buttons');
                nextButton.click(function(event) { removePreviousMarkers(inputValue); offset = offset+max_rows; fillSearchField(inputValue) });
            }
        } else {
            $('#search_next').remove();
            $('#search_prev').remove();
        }
    }

    function getFeature(geojsonStr) {
        var feature;
        var features = new OpenLayers.Format.GeoJSON({}).read(geojsonStr);
        if (features != null && features.length > 0) {
            feature = features[0];
//            feature.geometry = OpenLayers.Projection.transform(feature.geometry,geographic, mercator);
        }
        return feature;
    }

    function removePreviousMarkers(key) {
        function remove(entry) {
            var feature = entry.admin_center;
            if (feature) {
                townHallLayer.removeFeatures([feature]);
            }
        }
        var old = resultList[key];
        if (old) {
            $.map(old,remove);
        }
        if (popup) {
            map.removePopup(popup);
            popup = null;
        }
    }

    function addMarkers(request_term) {
        var i=offset;
        var len = resultList[request_term].length;
        var num = (offset + max_rows) > len ? len : offset + max_rows
        for (; i<num;i++) {
            var admin_center = resultList[request_term][i].admin_center;
            if (admin_center) townHallLayer.addFeatures([admin_center]);
        }
    }

    function buildResultList() {
        var frame = $('<div/>', {
                        class: 'ui-widget',
                        id: 'search_result_content'
                    });

        var heading = $('<h3>');
        var text = document.createTextNode(LANG.search_result_text);
        heading.append(text);

        var infoText = $('<div/>', {
                                 id: 'num_search_result' 
                         });
        var list = $('<div/>', {
                        id: 'log',
                        class: 'ac_results'
                    });
        var buttons = $('<div>', {
                           id: 'search_buttons'
                       });

        $('#instance_search').append(frame);
        frame.append(heading);
        frame.append(infoText);
        frame.append(list);
        frame.append(buttons);
    }

    var stopAutocompletion = false;
    var currentSearch;
    function querySearchResult() {
        stopAutocompletion = true;
        var request_term = $( "#instances" ).val();
        if (!currentSearch || currentSearch != request_term) {
            currentSearch = request_term;
            if (request_term.length > 2 && request_term != "Enter zip code or region") {
                $( "#instances" ).autocomplete("close");
                $.ajax({
                    beforeSend: function(jqXHR, settings) {
                        $('#instances').addClass('ui-autocomplete-loading');
                        return true;
                    },
                    url: 'find_instances.json',
                    dataType: "jsonp",
                    data: {
                        name_contains: request_term
                    },
                    success: function(data) {
                        $('#instances').removeClass('ui-autocomplete-loading');
                        resultList[request_term] = $.map( data.search_result, function( item ) {
                            var feature = getFeature(item.admin_center);
                            return {
                                instance_id: item.instance_id,
                                region_id: item.region_id,
                                label: item.name,
                                url: item.url,
                                value: item.name,
                                num_proposals: item.num_proposals,
                                num_papers: item.num_papers,
                                num_members: item.num_members,
                                create_date: item.create_date,
                                bbox: item.bbox,
                                admin_center: feature,
                                admin_type: item.admin_type,
                                is_in: item.is_in
                            }
                        });
                        currentSearch = undefined;
                        showSearchResult();
                    },
                    error: function(xhr,err) {
                        currentSearch = undefined;
                        $('#instances').removeClass('ui-autocomplete-loading');
                        //console.log('No response from server, sorry. url: ' + url + ', Error: '+err);
                        //alert('No response from server, sorry. Error: '+err);
                    }
                });
            }
        }
    }

    function showSearchResult() {
        removePreviousMarkers(prevInputValue);
        offset = 0;
        prevInputValue = new String(inputValue);
        inputValue = new String($( "#instances" ).val());

        if (resultList[inputValue]) {

            if ($('#instance_search').children().size() == 1) {
                buildResultList();    
            }

            fillSearchField(inputValue);
            var bounds = new OpenLayers.Bounds();
            var found = false;
            for (i=0; i<resultList[inputValue].length; i++) {
                var hit = resultList[inputValue][i];
                //if (hit.instance_id != "") {
                    var bbox = JSON.parse( hit.bbox );
                    var hitBounds = new OpenLayers.Bounds.fromArray(bbox);//.transform(geographic, mercator);
                    bounds.extend(hitBounds);
                    found = true;
                //}
            }
            if (found) {
                map.zoomToExtent(bounds)
            }
            //delete resultList[inputValue];
        }
    }

    $( "#instances" ).keypress(function(event) {
        if ( event.which == 13 || event.which == 10 ) {
            querySearchResult();
        }
    });

    $('#search_button').click(querySearchResult);

    $( "#instances" ).autocomplete({
        search: function(event, ui) {
            stopAutocompletion = false;
        },
        source: function( request, response ) {
            $.ajax({
                url: "/autocomplete_instances.json",
                dataType: "jsonp",
                data: {
//                    max_rows: 5,
//                    offset: offset,
                    name_contains: request.term
                },
                success: function( data ) {
                    if (!stopAutocompletion) {
                        response( $.map(data.search_result, function ( item ) {
                            return {
                                label: item.name,
                                value: item.name
                            }
                        }));
                    }
                }
            });
        },
        minLength: 2,
        open: function() {
            $( this ).removeClass( "ui-corner-all" ).addClass( "ui-corner-top" );
        },
        close: function() {
           $( "#instances" ).removeClass( "ui-corner-top" ).addClass( "ui-corner-all" );
        }

  });
}

var openlayers_url = $('#openlayers_url_field').val()
if (openlayers_url != "") {
    function noPositionClicked(instanceKey) {
        $('<a>', {
            id: 'create_geo_button', 
            class: 'button_small',
            click: addGeoTagHandler 
        }).append(document.createTextNode(LANG.add_position_text)).appendTo('#map_div');
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
        }).append(document.createTextNode(LANG.no_position_text)).appendTo('#map_div');
        $('<a/>').appendTo('#map_div');

        $('<div />', {
           id: 'map',
           class: 'edit_map'
        }).appendTo('#map_div');

        loadSingleProposalMap(openlayers_url, instanceKey, null, true, position);

        $('#create_geo_button').remove(); 

        $('<div />', { 
            id: 'attribution_div',
            class: 'note_map'
        }).appendTo('#map_div');

        $('#attribution_div').append('&copy; ');
        var osm_link = $('<a>', {
            href: 'http://www.openstreetmap.org/'
        });
        osm_link.appendTo('#attribution_div');
        osm_link.append(document.createTextNode('OpenStreetMap'));
        $('#attribution_div').append(document.createTextNode('-' + LANG.osm_cartographer_text + '('));
        var license_link = $('<a>', {
            href: 'http://creativecommons.org/licenses/by-sa/2.0/'
        });
        license_link.appendTo('#attribution_div');
        license_link.append(document.createTextNode(LANG.license_text));
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
}
