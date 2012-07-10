/*jslint browser: true, vars: true, plusplus: true, sloppy: true */
/*global $: true, OpenLayers: true, LANG: true */


/**
 * Javascript application code for adhocracy geo branch
 * mainly using openlayers, knockout.js and jquery
 *
 * @module adhocracy.geo
 *
 */

$.ajaxSetup({
    cache: true
});

// Make sure we have an "adhocracy" and namespace.
var adhocracy = adhocracy || {};

(function () {

    "use strict";

    /***************************************************
     * @namespace: adhocracy.geo
     ***************************************************/

    adhocracy.namespace('adhocracy.geo');

    adhocracy.geo.NUM_ZOOM_LEVELS = 14;
    adhocracy.geo.layersWithPopup = [];

    adhocracy.geo.inputValue = "";
    adhocracy.geo.prevInputValue = "";

    adhocracy.geo.styleProps = {
        pointRadius: 5,
        fillColor: "#f28686",
        fillOpacity: 0.8,
        strokeColor: "#be413f",
        strokeWidth: 1,
        strokeOpacity: 0.8
    };

    adhocracy.geo.styleTransparentProps = {
        pointRadius: 5,
        fillColor: "#ffffff",
        fillOpacity: 0.0,
        strokeColor: "#ffffff",
        strokeWidth: 1,
        strokeOpacity: 0.0
    };

    adhocracy.geo.styleSelect = {
        pointRadius: 5,
        fillColor: "#e82b2b",
        fillOpacity: 0.8,
        strokeColor: "#be413f",
        strokeWidth: 1,
        strokeOpacity: 0.8
    };

    adhocracy.geo.styleBorder = {
        fillColor: "#ffcc66",
        fillOpacity: 0.0,
        strokeWidth: 1,
        strokeColor: "#444444"
    };

    adhocracy.geo.styleRegionBorder = {
        fillColor: "#ffcc66",
        fillOpacity: 0.0,
        strokeWidth: 2,
        strokeColor: "#444444"
    };

    adhocracy.geo.styleArea = {
        fillColor: "#66ccff",
        fillOpacity: 0.5,
        strokeColor: "#3399ff"
    };

    adhocracy.geo.easteregg = false;
    adhocracy.geo.styleEasteregg = {
        fillColor: "#86f286",
        fillOpacity: 0.3,
        strokeOpacity: 0.3
    };


    adhocracy.geo.createProposalLayer = function () {

        return new OpenLayers.Layer.Vector("proposal", {
            displayInLayerSwitcher: false,
            styleMap: new OpenLayers.StyleMap({
                'default': new OpenLayers.Style(adhocracy.geo.styleProps),
                'select': new OpenLayers.Style(adhocracy.geo.styleSelect)
            })
        });
    };

    adhocracy.geo.fetchSingleProposal = function (singleProposalId, layer, callback) {
        var url = '/proposal/' + singleProposalId + '/get_geotag';
        $.ajax({
            url: url,
            success: function (data) {
                var features = new OpenLayers.Format.GeoJSON({}).read(data);
                if (features) {
                    // assert(features.length==1);
                    var feature = features[0];
                    $('#proposal_geotag_field').val(new OpenLayers.Format.GeoJSON({}).write(feature));
                    layer.addFeatures([feature]);
                    callback(feature);
                } else {
                    callback(null);
                }
            },
            error: function (xhr, err) {
            //console.log('No response from server, sorry. url: ' + url + ', Error: '+err);
                //alert('No response from server, sorry. Error: '+err);
            }
        });
    };

    adhocracy.geo.balloonSymbolizer = {
        graphicHeight: 31,
        graphicWidth: 24,
        graphicYOffset: -31
    };

    adhocracy.geo.townHallSymbolizer = {
        externalGraphic: '/images/map_hall_pink.png',
        graphicHeight: 12,
        graphicWidth: 16,
        graphicYOffset: -12
    };

    adhocracy.geo.setBalloonSymbolizer = function (scope, idx) {
        var letter = String.fromCharCode(idx + 97);
        scope.symbolizer = adhocracy.geo.balloonSymbolizer;
        scope.symbolizer.externalGraphic = '/images/map_marker_pink_' + letter + '.png';
        return letter;
    };

    adhocracy.geo.setTownHallSymbolizer = function (scope, idx) {
        scope.symbolizer = adhocracy.geo.townHallSymbolizer;
        if (idx === undefined) {
            scope.symbolizer.externalGraphic = '/images/map_hall_pink.png';
            return undefined;
        }
        var letter = String.fromCharCode(idx + 97);
        scope.symbolizer.externalGraphic = '/images/map_hall_pink_' + letter + '.png';
        return letter;
    };


    adhocracy.geo.createTownHallLayer = function () {
        return new OpenLayers.Layer.Vector('instance_town_hall', {
            displayInLayerSwitcher: false,
            styleMap: new OpenLayers.StyleMap({
                'default': adhocracy.geo.townHallSymbolizer, //new OpenLayers.Style(adhocracy.geo.styleProps),
                'select': adhocracy.geo.townHallSymbolizer //new OpenLayers.Style(adhocracy.geo.styleSelect)
            })
        });
    };

    adhocracy.geo.createOverviewLayers = function () {

        var boundaryLayer = new OpenLayers.Layer.Vector('overview', {
            displayInLayerSwitcher: false,
            styleMap: new OpenLayers.StyleMap({
                'default': new OpenLayers.Style(adhocracy.geo.styleBorder)
            })
        });

        var townHallLayer = adhocracy.geo.createTownHallLayer();
        var url = '/instance/get_all_instance_regions.json';
        $.ajax({
            url: url,
            success: function (data) {
                var i = 0;
                var features = new OpenLayers.Format.GeoJSON({}).read(data);
                for (i = 0; i < features.length; i++) {
                    // assert(features.length==1);
                    var feature = features[0];
                    boundaryLayer.addFeatures([feature]);
                    //callback(feature);
                    if (feature.attributes.admin_center) {
                        var features2 = new OpenLayers.Format.GeoJSON({}).read(feature.attributes.admin_center);
                        var feature2 = features2[0];
                        townHallLayer.addFeatures([feature2]);
                    }
                }
    //            if (features.length == 0) {
    //                callback(null);
    //            }
            },
            error: function (xhr, err) {
                //console.log('No response from server, sorry. url: ' + url + ', Error: '+err);
                //alert('No response from server, sorry. Error: '+err);
            }
        });

        return [boundaryLayer, townHallLayer];

    };

    adhocracy.geo.createRegionProposalsLayer = function (instanceKey, initialProposals, featuresAddedCallback) {

        var rule = new OpenLayers.Rule({
            symbolizer: adhocracy.geo.balloonSymbolizer
        });
        rule.evaluate = function (feature) {
            if (initialProposals) {
                var index = initialProposals.indexOf(feature.fid);

                if (index >= 0) {
                    if (index < 10) {
                        var letter = adhocracy.geo.setBalloonSymbolizer(this, index);
                        $('#result_list_marker_' + feature.fid).attr('alt', letter).addClass('marker_' + letter);
                        return true;
                    }
                    $('#result_list_marker_' + feature.fid).attr('alt', index).addClass('bullet_marker');
                }
            }
            return false;
        };

        var format = new OpenLayers.Format.GeoJSON();
        format.read = function () {
            var result = OpenLayers.Format.GeoJSON.prototype.read.apply(this, arguments);
            if (result.length === 0) {
                var features = {};
                features.features = [];
                featuresAddedCallback(features);
            }
            return result;
        };

        var layer = new OpenLayers.Layer.Vector('region_proposals', {
            strategies: [new OpenLayers.Strategy.Fixed()],
            protocol: new OpenLayers.Protocol.HTTP({
                url: '/instance/' + instanceKey + '/get_proposal_geotags',
                format: format
            }),
            styleMap: new OpenLayers.StyleMap({
                'default': new OpenLayers.Style(adhocracy.geo.styleProps, {
                    rules: [
                        rule,
                        new OpenLayers.Rule({
                            elseFilter: true
                        })
                    ]
                }),
                'select': new OpenLayers.Style(adhocracy.geo.styleSelect)
            })
        });

        layer.events.on({
            'featuresadded': featuresAddedCallback
        });

        return layer;
    };

    adhocracy.geo.createPopupControl = function (map, layer, buildPopupContent) {

        function openPopup(event) {
            adhocracy.geo.popup = new OpenLayers.Popup.FramedCloud("singlepopup",
                event.feature.geometry.getBounds().getCenterLonLat(),
                null,
                buildPopupContent(event.feature.attributes),
                null, false, null);
            map.addPopup(adhocracy.geo.popup);
        }

        function closePopup(event) {
            if (adhocracy.geo.popup) {
                map.removePopup(adhocracy.geo.popup);
                adhocracy.geo.popup = null;
            }
        }

        layer.events.on({
            'featureselected': openPopup,
            'featureunselected': closePopup
        });

        adhocracy.geo.layersWithPopup.push(layer);

    };

    adhocracy.geo.addEditControls = function (map, layer) {

        var buttonState;
        var pointClicked, addChangeRemoveGeoButton, addAddGeoButton;

        var pointControl = new OpenLayers.Control.DrawFeature(layer, OpenLayers.Handler.Point, {
            featureAdded: function (feature) {
                pointClicked();
            }
        });

        function updateEditButtons() {

            var new_state = layer.features.length;

            if (buttonState !== new_state) {

                if (buttonState === 0) {
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

        addAddGeoButton = function () {
            $('<a />', {
                id: 'add_geo_button',
                'class': 'button',
                click: function () {
                    //propslayer. OpenLayers.Handler.Click({single:true, stopSingle:true});
                    pointControl.activate();
                },
                // FIXME: Use Gettext
                // text: 'Add position'
                text: LANG.set_position_text
            }).appendTo('#edit_map_buttons');
        };

        addChangeRemoveGeoButton = function () {
            $('<a />', {
                id: 'change_geo_button',
                'class': 'button',
                click: function () {
                    //propslayer. OpenLayers.Handler.Click({single:true, stopSingle:true});
                    layer.removeAllFeatures();
                    pointControl.activate();
                },
                text: LANG.set_different_position_text
            }).appendTo('#edit_map_buttons');

            $('<a />', {
                id: 'remove_geo_button',
                'class': 'button',
                click: function () {
                    layer.removeAllFeatures();
                    $('#proposal_geotag_field').val('');
                    updateEditButtons();
                },
                text: LANG.remove_position_text
            }).appendTo('#edit_map_buttons');
        };

        function updateGeotagField() {
            var transformed_feature = layer.features[0].clone();
            $('#proposal_geotag_field').val(new OpenLayers.Format.GeoJSON({}).write(transformed_feature));
            map.setCenter(layer.features[0].geometry.getBounds().getCenterLonLat(),
                map.getZoom());
        }

        pointClicked = function () {
            pointControl.deactivate();
            updateEditButtons();
            updateGeotagField();
        };

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
                onComplete: function (feature, pixel) {
                    updateGeotagField();
                },
                autoActivate: true
            }),
            pointControl
        ]);

        return singleProposalFetched;
    };

    adhocracy.geo.createRegionBoundaryLayer = function (instanceKey, callback) {

        var layer = new OpenLayers.Layer.Vector('instance_boundary', {
            displayInLayerSwitcher: false,
            styleMap: new OpenLayers.StyleMap({
                'default': new OpenLayers.Style(adhocracy.geo.styleRegionBorder)
            })
        });

        var townHallLayer = adhocracy.geo.createTownHallLayer();

        var url = '/instance/' + instanceKey + '/get_region';
        $.ajax({
            url: url,
            success: function (data) {
                var features = new OpenLayers.Format.GeoJSON({}).read(data);
                if (features) {
                    // assert(features.length==1);
                    var feature = features[0];
                    layer.addFeatures([feature]);
                    callback(feature);
                    if (feature.attributes.admin_center) {
                        var features2 = new OpenLayers.Format.GeoJSON({}).read(feature.attributes.admin_center);
                        var feature2 = features2[0];
                        townHallLayer.addFeatures([feature2]);
                    }
                } else {
                    callback(null);
                }
            },
            error: function (xhr, err) {
                //console.log('No response from server, sorry. url: ' + url + ', Error: '+err);
                //alert('No response from server, sorry. Error: '+err);
            }
        });

        return [layer, townHallLayer];
    };

    adhocracy.geo.createEastereggLayer = function () {
        var url = '/javascripts/easteregg.json';
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
            styleMap: new OpenLayers.StyleMap({
                'default': adhocracy.geo.styleEasteregg
            })
        });

        return layer;
    };

    adhocracy.geo.layerHasFeature = function (layer, feature) {
        var i = 0;
        for (i = 0; i < layer.features.length; i++) {
            if (layer.features[i].attributes.region_id === feature.attributes.region_id) {
                return true;
            }
        }
        return false;
    };

    /* REFACT: unused */
    adhocracy.geo.listHasFeature = function (list, feature) {
        var i = 0;
        for (i = 0; i < list.length; i++) {
            if (list[i].region_id === feature.attributes.region_id) {
                return true;
            }
        }
        return false;
    };

    adhocracy.geo.createInstanceDesc = function (item) {
        return item.num_proposals + ' '
                + LANG.proposals_text + ' \u00B7 '
                + item.num_papers + ' '
                + LANG.papers_text + ' \u00B7 '
                + item.num_members + ' '
                + LANG.members_text + ' \u00B7 '
                + LANG.creation_date_text + ' '
                + item.create_date;
    };

    adhocracy.geo.buildInstancePopup = function (attributes) {

        var result = "<div class='instance_popup_title'>";
        if (attributes.url) {
            result = result + "<a href='" + attributes.url + "'>";
        }
        var label = attributes.label;
        if (attributes.admin_type) {
            label = label + " (" + attributes.admin_type + ")";
        }
        result = result + label;
        if (attributes.url) {
            result = result + "</a>";
        }
        if (attributes.instance_id != "") {
            var desc = adhocracy.geo.createInstanceDesc(attributes);
            result = result + "<div class='meta'>" + desc + "</div>";
        }
        result = result + "</div>";
        return result;
    };


    /* Stuff used by adhocracy.geo.addTiledTownhallLayer and adhocracy.geo.addMultiBoundaryLayer */

    adhocracy.geo.adminLevels = [4, 5, 6, 7, 8];

    //Zoom 0 ... 14 -> 0=hidden, 1=borderColor1, 2=borderColor2, 3=borderColor3, ...]
    adhocracy.geo.displayMap = [
        {styles: [1, 0, 0, 0, 0]},
        {styles: [1, 0, 0, 0, 0]},
        {styles: [1, 0, 0, 0, 0]},
        {styles: [1, 0, 1, 0, 0]},
        {styles: [1, 0, 1, 0, 0]},  //4
        {styles: [0, 0, 1, 1, 0]},
        {styles: [0, 0, 1, 1, 0]},
        {styles: [0, 0, 1, 1, 1]},
        {styles: [0, 0, 1, 1, 1]},  //8
        {styles: [0, 0, 1, 1, 1]},
        {styles: [0, 0, 1, 1, 1]},
        {styles: [0, 0, 1, 1, 1]},
        {styles: [0, 0, 1, 1, 1]},  //12
        {styles: [0, 0, 1, 1, 1]},
        {styles: [0, 0, 1, 1, 1]}
    ];

    adhocracy.geo.makeTiles = function (sizeLL, bounds) {
        var xStart = Math.floor(bounds.left / sizeLL);
        var yStart = Math.floor(bounds.bottom / sizeLL);
        var tiles = [];
        var x = xStart;
        do {
            var y = yStart;
            do {
                tiles.push({
                    x: x,
                    y: y
                });
                y += 1;
            } while ((y * sizeLL) < bounds.top);
            x += 1;
        } while ((x * sizeLL) < bounds.right);
        return tiles;
    };

    adhocracy.geo.alreadyFetched = function (tiles, tile) {
        var fetch = true;
        var i = 0;
        for (i = 0; i < tiles.length; i++) {
            if (tile.x === tiles[i].x && tile.y === tiles[i].y) {
                fetch = false;
            }
        }
        return !fetch;
    };

    adhocracy.geo.getLayerIndex = function (admin_level) {
        return adhocracy.geo.adminLevels.indexOf(admin_level);
    };

    adhocracy.geo.addTiledTownhallLayer = function (map, resultList) {
        var addTownHalls;
        var townHallTiles = new Array(adhocracy.geo.adminLevels.length);
        var i = 0;
        for (i = 0; i < adhocracy.geo.adminLevels.length; i++) {
            townHallTiles[i] = [];
        }
        var townHallLayer = adhocracy.geo.createTownHallLayer();

        function fetchTownHalls(bounds, adminLevel, townHallTiles) {
            //fetch townHalls
            var tileSize = 256;
            var tileSizeLL = tileSize * map.getResolution();
            var newTiles = adhocracy.geo.makeTiles(tileSizeLL, bounds);
            var i = 0;

            function success(data) {
                addTownHalls(data, adminLevel);
            }
            function error(data) {
                // console.log("error: " +err);
            }

            for (i = 0; i < newTiles.length; i++) {
                var fetch = !adhocracy.geo.alreadyFetched(townHallTiles, newTiles[i]);
                if (fetch) {
                    townHallTiles.push(newTiles[i]);
                    var url = '/get_admin_centres.json'
                                    + '?x=' + newTiles[i].x
                                    + '&y=' + newTiles[i].y
                                    + '&zoom=' + map.getZoom()
                                    + '&admin_level=' + adminLevel;
                    $.ajax({
                        url: url,
                        success: success,
                        error: error
                    });
                }
            }
        }

        addTownHalls = function (data, adminLevel) {
            var features = new OpenLayers.Format.GeoJSON({}).read(data);
            var i = 0;
            for (i = 0; i < features.length; i++) {
                var feature = features[i];
                if (feature.geometry !== null && !adhocracy.geo.layerHasFeature(townHallLayer, feature)) {
                    townHallLayer.addFeatures([feature]);
                }
            }
        };

        var moveTownHallTo = function (bounds, zoomChanged, dragging) {
            OpenLayers.Layer.Vector.prototype.moveTo.apply(this, arguments);
            var zoom = map.getZoom();
            var i = 0;
            while (i < adhocracy.geo.adminLevels.length) {
                var style = adhocracy.geo.displayMap[zoom]['styles'][i];
                if (style === 1 || style === 2) {
                    fetchTownHalls(bounds, adhocracy.geo.adminLevels[i], townHallTiles[i]);
                }
                i++;
            }
        };

        function isInstance(feature, searchEntry) {
            return (searchEntry.region_id === feature.attributes.region_id
                    && searchEntry.instance_id != "");
        }

        function isRegion(feature, searchEntry) {
            return (searchEntry.region_id === feature.attributes.region_id
                    && searchEntry.instance_id == "");
        }

        function getRegionNum(feature) {
            if (resultList) {
                if (resultList[adhocracy.geo.inputValue]) {
                    var result = resultList[adhocracy.geo.inputValue];
                    var i = 0;
                    var numRegion = 0;
                    for (i = 0; i < result.length; i++) {
                        if (isRegion(feature, result[i])) {
                            return numRegion;
                        }
                        if (result[i].instance_id == "") {
                            numRegion = numRegion + 1;
                        }
                    }
                }
            }
            throw "feature not found in search result";
        }

        //pre: feature is in search result list
        function getInstanceNum(feature) {
            if (resultList) {
                if (resultList[adhocracy.geo.inputValue]) {
                    var result = resultList[adhocracy.geo.inputValue];
                    var i = 0;
                    var numInstance = 0;
                    for (i = 0; i < result.length; i++) {
                        if (isInstance(feature, result[i])) {
                            return numInstance;
                        }
                        if (result[i].instance_id != "") {
                            numInstance = numInstance + 1;
                        }
                    }
                }
            }
            throw "feature not found in search result";
        }

        function isInstanceInSearch(feature) {
            if (resultList) {
                if (resultList[adhocracy.geo.inputValue]) {
                    var result = resultList[adhocracy.geo.inputValue];
                    var i = 0;
                    for (i = 0; i < result.length; i++) {
                        if (isInstance(feature, result[i])) {
                            return true;
                        }
                    }
                }
            }
            return false;
        }

        function isRegionInSearch(feature) {
            if (resultList) {
                if (resultList[adhocracy.geo.inputValue]) {
                    var result = resultList[adhocracy.geo.inputValue];
                    var i = 0;
                    for (i = 0; i < result.length; i++) {
                        if (isRegion(feature, result[i])) {
                            return true;
                        }
                    }
                }
            }
            return false;
        }

        function filterInstancesBalloon(feature) {
            var idx;
            if (isInstanceInSearch(feature)) {
                idx = getInstanceNum(feature);
                adhocracy.geo.setBalloonSymbolizer(this, idx);
                return true;
            }
            if (isRegionInSearch(feature)) {
                idx = getRegionNum(feature);
                adhocracy.geo.setTownHallSymbolizer(this, idx);
                return true;
            }
            return false;
        }

        function filterElse(feature) {
            adhocracy.geo.setTownHallSymbolizer(this, undefined);
            return true;
        }

        function filterInstancesInVisible(feature) {
            if (isInstanceInSearch(feature) || isRegionInSearch(feature)) {
                return false;
            }
            var zoom = map.getZoom();
            var adminLevel = feature.attributes.admin_level;
            var layerIdx = adhocracy.geo.getLayerIndex(adminLevel);
            var style = adhocracy.geo.displayMap[zoom]['styles'][layerIdx];
            return (style === 0);
        }

        var rule = new OpenLayers.Rule({symbolizer: adhocracy.geo.balloonSymbolizer});
        rule.evaluate = filterInstancesBalloon;
        var rule2 = new OpenLayers.Rule({ symbolizer: adhocracy.geo.styleTransparentProps });
        rule2.evaluate = filterInstancesInVisible;
        var rule3 = new OpenLayers.Rule({elseFilter: true, symbolizer: adhocracy.geo.townHallSymbolizer});
        rule3.evaluate = filterElse;

        townHallLayer.styleMap = new OpenLayers.Style(adhocracy.geo.styleProps, {rules: [rule, rule2, rule3]});
        townHallLayer.moveTo = moveTownHallTo;
        map.addLayer(townHallLayer);
        adhocracy.geo.createPopupControl(map, townHallLayer, adhocracy.geo.buildInstancePopup);

        return townHallLayer;
    };

    adhocracy.geo.addMultiBoundaryLayer = function (map, layers, tiles) {

        function isValidAdminLevel(admin_level) {
            var i = 0;
            for (i = 0; i < adhocracy.geo.adminLevels.length; i++) {
                if (adhocracy.geo.adminLevels[i] === admin_level) {
                    return true;
                }
            }
            return false;
        }


        function redrawFeatures(thelayer, thestyle) {
            var i = 0;
            for (i = 0; i < thelayer.features.length; i++) {
                thelayer.features[i].style = thestyle;
                thelayer.drawFeature(thelayer.features[i], thestyle);
            }
        }

        var moveMapTo = function (bounds, zoomChanged, dragging) {
            var zoom = map.getZoom();
            if (zoom != null && zoomChanged != null) {
                var i = 0;
                while (i < adhocracy.geo.adminLevels.length) {
                    var styleChanged = adhocracy.geo.displayMap[zoomChanged]['styles'][i];
                    var style = adhocracy.geo.displayMap[zoom]['styles'][i];
                    var j = 0;
                    for (j = 0; j < adhocracy.geo.displayMap.length; j++) {
                        layers[i][j].setVisibility(false);
                    }
                    if (styleChanged !== 0) {
                        layers[i][zoomChanged].setVisibility(true);
                        if (style !== styleChanged) {
                            var k = 0;
                            if (styleChanged < 2) {
                                for (k = 0; k < adhocracy.geo.displayMap.length; k++) {
                                    layers[i][k].styleMap['default']
                                        = new OpenLayers.Style(adhocracy.geo.styleBorder);
                                    layers[i][k].styleMap['default']
                                        = new OpenLayers.Style(adhocracy.geo.styleBorder);
                                    redrawFeatures(layers[i][k], adhocracy.geo.styleBorder);
                                }
                            } else {
                                for (k = 0; k < adhocracy.geo.displayMap.length; k++) {
                                    layers[i][k].styleMap['default']
                                        = new OpenLayers.Style(styleArea);
                                    layers[i][k].styleMap['default']
                                        = new OpenLayers.Style(adhocracy.geo.styleArea);
                                    redrawFeatures(layers[i][k], adhocracy.geo.styleArea);
                                }
                            }
                        }
                    }
                    i++;
                }
            }

            OpenLayers.Map.prototype.moveTo.apply(this, arguments);
        };

        function addBoundaryPaths(zoom, data) {
            var features = new OpenLayers.Format.GeoJSON({}).read(data);
            if (features) {
                var k = 0;
                for (k = 0; k < features.length; k++) {
                    var feature = features[k];
                    if (feature.geometry !== null) {
                        var admin_level = parseInt(feature.attributes.admin_level, 10);
                        var zoom2 = parseInt(feature.attributes.zoom, 10);
                        if (zoom2 >= 0 && zoom2 < 15 && isValidAdminLevel(admin_level)) {
                            layers[adhocracy.geo.getLayerIndex(admin_level)][zoom2].addFeatures([feature]);
                        }
                    }
                }
            }
        }

        var moveLayersTo = function (bounds, zoomChanged, dragging) {
            var showGrid = false;
            var zoom = this.zoom;

            function success(data) {
                addBoundaryPaths(zoom, data);
            }
            function error(xhr, err) {
                // console.log("error: " + err);
            }
            if (this.getVisibility()) {
                var tileSize = 256;
                var tileSizeLL = tileSize * map.getResolution();
                var newTiles = adhocracy.geo.makeTiles(tileSizeLL, bounds);
                var i = 0;
                for (i = 0; i < newTiles.length; i++) {
                    if (!adhocracy.geo.alreadyFetched(tiles[this.layersIdx], newTiles[i])) {
                        tiles[this.layersIdx].push(newTiles[i]);
                        if (showGrid) {
                            var box = new OpenLayers.Bounds(newTiles[i].x * tileSizeLL, newTiles[i].y * tileSizeLL,
                                                        (newTiles[i].x + 1) * tileSizeLL, (newTiles[i].y + 1) * tileSizeLL);
                            layers[this.layersIdx][zoom].addFeatures([new OpenLayers.Feature.Vector(box.toGeometry(),
                                                                                                            {})]);
                        }
                        var url = '/get_tiled_boundaries.json'
                                        + '?x=' + newTiles[i].x
                                        + '&y=' + newTiles[i].y
                                        + '&zoom=' + zoom
                                        + '&admin_level=' + adhocracy.geo.adminLevels[this.layersIdx];
                        $.ajax({
                            url: url,
                            success: success,
                            error: error
                        });
                    }
                }
            }
            OpenLayers.Layer.Vector.prototype.moveTo.apply(this, arguments);
        };

        var layersIdx = 0;
        while (layersIdx < adhocracy.geo.adminLevels.length) {
            var style = adhocracy.geo.displayMap[map.getZoom()]['styles'][layersIdx];

            layers[layersIdx] = new Array(adhocracy.geo.displayMap.length);
            tiles[layersIdx] = [];
            var z;
            for (z = 0; z < adhocracy.geo.displayMap.length; z++) {
                var layername = "layer" + adhocracy.geo.adminLevels[layersIdx] + z;

                layers[layersIdx][z]
                    = new OpenLayers.Layer.Vector(layername, {
                        displayInLayerSwitcher: false,
                        styleMap: new OpenLayers.StyleMap({'default': (style < 2 ? new OpenLayers.Style(adhocracy.geo.styleBorder) : new OpenLayers.Style(adhocracy.geo.styleArea))}),
                        layersIdx: layersIdx,
                        zoom: z
                    });
                layers[layersIdx][z].moveTo = moveLayersTo;
                map.addLayer(layers[layersIdx][z]);
            }
            layersIdx++;
        }
        map.moveTo = moveMapTo;

        //var foldLayers = adhocracy.geo.foldLayerMatrix(layers);
        //return foldLayers;
        return undefined;
    };

    adhocracy.geo.addUntiledTownhallLayer = function (map, resultList) {
        var townHallLayer = adhocracy.geo.createTownHallLayer();

        $.ajax({
            url: '/instance/get_all_instance_centres.json',
            success: function (data) {
                var features = new OpenLayers.Format.GeoJSON({}).read(data);
                var i = 0;
                for (i = 0; i < features.length; i++) {
                    var feature = features[i];
                    if (feature.geometry !== null) {
                        townHallLayer.addFeatures([feature]);
                    }
                }
            },
            error: {}
        });

        map.addLayer(townHallLayer);
        adhocracy.geo.createPopupControl(map, townHallLayer, adhocracy.geo.buildInstancePopup);
        return townHallLayer;
    };

    /* REFACT: only used in outcommented code */
    adhocracy.geo.foldLayerMatrix = function (layers) {
        var foldLayers = [];
        var i = 0, j = 0;
        for (i = 0; i < layers.length; i++) {
            for (j = 0; j < layers[i].length; j++) {
                foldLayers = foldLayers.concat(layers[i][j]);
            }
        }
        return foldLayers;
    };


    adhocracy.geo.createBaseLayers = function (blank) {

        var osmOptions = {
            displayInLayerSwitcher: true,
            zoomOffset: 5,
            numZoomLevels: adhocracy.geo.NUM_ZOOM_LEVELS,
            maxResolution: 4891.9698095703125,
            tileOptions: {crossOriginKeyword: null}
        };

        var baseLayers = [
            // top definition is selected by default
            new OpenLayers.Layer.OSM("OSM Admin Boundaries",
                        "http://129.206.74.245:8007/tms_b.ashx?x=${x}&y=${y}&z=${z}", osmOptions),
            // default Openstreetmap Baselayer
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
            baseLayers.push(new OpenLayers.Layer("Blank", {isBaseLayer: true}));
        }

        return baseLayers;
    };


    adhocracy.geo.createMap = function () {

        // The bounds below correspond to the following bounds in geographic
        // projection:
        // var RESTRICTED_BOUNDS = new OpenLayers.Bounds(0, 40, 30, 60);

        var RESTRICTED_BOUNDS = new OpenLayers.Bounds(
            0,
            4865942.278825832,
            3339584.7233333336,
            8399737.888649108
        );

        // FALLBACK_BOUNDS is the BBOX around Germany. In geographic projection:
        // var FALLBACK_BOUNDS = [5.86630964279175, 47.2700958251953, 15.0419321060181, 55.1175498962402];
        // In spherical mercartor projection:

        adhocracy.geo.FALLBACK_BOUNDS = new OpenLayers.Bounds(
            653034.6021803395,
            5986272.559465266,
            1674460.2223558303,
            7384713.654445262
        );

        return new OpenLayers.Map('map', {
            restrictedExtent: RESTRICTED_BOUNDS,
            projection: "EPSG:900913",
            controls: []
        });
    };


    adhocracy.geo.createControls = function (fullControls, keyboardControls) {
        // add map controls

        var mapControls = [
            new OpenLayers.Control.Navigation({'handleRightClicks': true}),
            new OpenLayers.Control.ScaleLine()
        ];

        if (fullControls) {
            mapControls.push(new OpenLayers.Control.PanZoomBar());
            mapControls.push(new OpenLayers.Control.LayerSwitcher());
            // MousePosition currently displays 900913 instead of 4236
            // mapControls.push(new OpenLayers.Control.MousePosition());
            mapControls.push(new OpenLayers.Control.Scale());
            // mapControls.push(new OpenLayers.Control.Graticule());
        } else {
            mapControls.push(new OpenLayers.Control.ZoomPanel());
    //        mapControls.push(new OpenLayers.Control.ZoomOut());
        }
        if (keyboardControls) {
            // use KeyboardDefault only when map is the central element
            mapControls.push(new OpenLayers.Control.KeyboardDefaults());
        }

        return mapControls;
    };



    /* REFACT: unused */
    adhocracy.geo.centerMap = function (map, feature, boundary) {
        if (feature) {
            map.setCenter(feature.geometry.getBounds().getCenterLonLat(), 10);
            // x boundary
        } else {
            map.setCenter(feature.geometry.getBounds().getCenterLonLat(), 10);
            // nur boundary
        }
    };


    adhocracy.geo.createWaiter = function (number, callback) {

        // waits for number of addFeature calls and finally calls callback

        var countdown = number;
        var bounds;

        var primaryBounds = new OpenLayers.Bounds();
        var secondaryBounds = new OpenLayers.Bounds();
        var primary_is_empty = true;
        var secondary_is_empty = true;

        function addFeature(feature, primary) {
            if (typeof primary === 'undefined') {
                primary = true;
            }
            countdown--;

            if (feature) {
                if (feature.features && feature.features instanceof Array) {
                    var i;
                    for (i = 0; i < feature.features.length; i++) {
                        if (primary) {
                            primaryBounds.extend(feature.features[i].geometry.getBounds());
                        } else {
                            secondaryBounds.extend(feature.features[i].geometry.getBounds());
                        }
                    }
                    if (feature.features.length > 0) {
                        if (primary) {
                            primary_is_empty = false;
                        } else {
                            secondary_is_empty = false;
                        }
                    }
                } else {
                    if (primary) {
                        primaryBounds.extend(feature.geometry.getBounds());
                        primary_is_empty = false;
                    } else {
                        secondaryBounds.extend(feature.geometry.getBounds());
                        secondary_is_empty = false;
                    }
                }
            }

            if (countdown === 0) {
                if (!primary_is_empty) {
                    var sz = primaryBounds.getSize();
                    if (sz.h === 0 && sz.w === 0 && !secondary_is_empty) {
                        var halfSz = secondaryBounds.getSize();
                        halfSz.w /= 4;
                        halfSz.h /= 4;
                        var center = primaryBounds.getCenterLonLat();
                        primaryBounds = new OpenLayers.Bounds(center.lon - halfSz.w,
                                                              center.lat - halfSz.h,
                                                              center.lon + halfSz.w,
                                                              center.lat + halfSz.h);
                    }
                    bounds = primaryBounds;
                } else if (!secondary_is_empty) {
                    bounds = secondaryBounds;
                } else {
                    bounds = adhocracy.geo.FALLBACK_BOUNDS;
                }
                callback(bounds);
            }
        }

        return addFeature;
    };

    adhocracy.geo.buildProposalPopup = function (attributes) {
        var maxPopupTitleLength = 30;
        var title = attributes.title;
        if (title.length > maxPopupTitleLength) {
            title = title.substring(0, maxPopupTitleLength) + " ...";
        }

        var result = "<div class='proposal_popup_title'>";
        result = result + "<a href='/proposal/" + attributes.region_id + "'>" + title + "</a>";
        result = result + "<div class='meta'>";
        result = result + attributes.num_for + ":" + attributes.num_against + " " + LANG.votes_text;
        result = result + ' \u00B7 ';
        result = result + attributes.num_norms + " " + LANG.norms_text;
        result = result + "</div>";
        result = result + "</div>";
        return result;
    };


    adhocracy.geo.buildEastereggPopup = function (attributes) {
        return "<div class='easteregg_popup_title'><img src='" + attributes.img + "'><br>" + attributes.text + "</div>";
    };


    adhocracy.geo.createSelectControl = function () {

        var selectControl = new OpenLayers.Control.SelectFeature(adhocracy.geo.layersWithPopup, {
                clickout: true,
                toggle: false,
                multiple: false,
                hover: false,
                toggleKey: "ctrlKey", // ctrl key removes from selection
                multipleKey: "shiftKey", // shift key adds to selection
                box: false,
                autoActivate: true
            });

        return selectControl;
    };

    adhocracy.geo.loadSingleProposalMap = function (openlayers_url, instanceKey, proposalId, edit, position) {
        $.getScript(openlayers_url, function () {

            var map = adhocracy.geo.createMap();

            var numFetches = 1;
            if (proposalId) {
                numFetches = 2;
            }
            var waiter = adhocracy.geo.createWaiter(numFetches, function (bounds) {
                map.zoomToExtent(bounds);
            });

            map.addControls(adhocracy.geo.createControls(edit, false));
            map.addLayers(adhocracy.geo.createBaseLayers());
            var regionBoundaryLayers = adhocracy.geo.createRegionBoundaryLayer(instanceKey, function (feature) {
                waiter(feature);
            });
            map.addLayers(regionBoundaryLayers);
            adhocracy.geo.createPopupControl(map, regionBoundaryLayers[1], adhocracy.geo.buildInstancePopup);

            var proposalLayer = adhocracy.geo.createProposalLayer();
            map.addLayer(proposalLayer);
            adhocracy.geo.createPopupControl(map, proposalLayer, adhocracy.geo.buildProposalPopup);

            var singleProposalFetchedCallback;
            if (edit) {
                singleProposalFetchedCallback = adhocracy.geo.addEditControls(map, proposalLayer);
            }

            //don't try to fetch proposals geotags when there's no proposal (i.e. if proposal is created)
            if (proposalId) {
                adhocracy.geo.fetchSingleProposal(proposalId, proposalLayer, function (feature) {
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
                        proposalLayer.addFeatures([feature]);
                    }
                }
                singleProposalFetchedCallback(feature);
            }
            if (adhocracy.geo.easteregg) {
                var easterLayer = adhocracy.geo.createEastereggLayer();
                map.addLayer(easterLayer);
                adhocracy.geo.createPopupControl(map, easterLayer, adhocracy.geo.buildEastereggPopup);
            }
            map.addControl(adhocracy.geo.createSelectControl());
        });
    };

    adhocracy.geo.enableMarker = function (id, layer, selectControl) {
        $('.' + id).click(function (event) {
            var target = event.target || event.srcElement;
            var feature = layer.getFeaturesByAttribute('region_id', parseInt(target.id.substring((id + '_').length), 10))[0];
            if (adhocracy.geo.popup) {
                var flonlat = feature.geometry.getBounds().getCenterLonLat();
                var plonlat = adhocracy.geo.popup.lonlat;
                selectControl.clickoutFeature(feature);
                if (plonlat !== flonlat) {
                    selectControl.clickFeature(feature);
                }
            } else {
                selectControl.clickFeature(feature);
            }
        });
    };

    adhocracy.geo.loadRegionMap = function (openlayers_url, instanceKey, initialProposals, largeMap, fullRegion) {
        $.getScript(openlayers_url, function () {

            var map;

            if (largeMap) {
                var top = $('#header').outerHeight() + $('#subheader').outerHeight() + $('#flash_message').outerHeight();
                $('#fullscreen_map').css('position', 'absolute').css('top', top + 'px').css('bottom', 0).css('width', '100%');
                $('#hide_list_icon').show();
                $('#hide_list_icon').click(function () {
                    $('#hide_list_icon').hide();
                    $('#left_block').fadeOut('normal', function () {
                        $('#central_block').css('width', '100%');
                        map.updateSize();
                    });
                    $('#show_list_icon').show();
                });
                $('#show_list_icon').click(function () {
                    $('#show_list_icon').hide();
                    $('#left_block').fadeIn('normal', function () {
                        $('#central_block').css('width', '70%');
                        map.updateSize();
                    });
                    $('#hide_list_icon').show();
                });
            }

            map = adhocracy.geo.createMap();

            var waiter = adhocracy.geo.createWaiter(fullRegion ? 1 : 2, function (bounds) {
                map.zoomToExtent(bounds);

                var controls;
                if (largeMap) {
                    controls = adhocracy.geo.createControls(true, true);
                } else {
                    controls = adhocracy.geo.createControls(false, false);
                }
                map.addControls(controls);
            });

            map.addLayers(adhocracy.geo.createBaseLayers());
            var regionBoundaryLayers = adhocracy.geo.createRegionBoundaryLayer(instanceKey, function (feature) {
                waiter(feature, false);
            });
            map.addLayers(regionBoundaryLayers);
            adhocracy.geo.createPopupControl(map, regionBoundaryLayers[1], adhocracy.geo.buildInstancePopup);

            var proposalLayer = adhocracy.geo.createRegionProposalsLayer(instanceKey, initialProposals, function (features) {
                if (!(fullRegion)) {
                    waiter(features, true);
                }
            });
            map.addLayer(proposalLayer);
            var popupControl = adhocracy.geo.createPopupControl(map, proposalLayer, adhocracy.geo.buildProposalPopup);

            if (adhocracy.geo.easteregg) {
                var easterLayer = adhocracy.geo.createEastereggLayer();
                map.addLayer(easterLayer);
                adhocracy.geo.createPopupControl(map, easterLayer, adhocracy.geo.buildEastereggPopup);
            }
            var selectControl = adhocracy.geo.createSelectControl();
            adhocracy.geo.enableMarker('result_list_marker', proposalLayer, selectControl);
            map.addControl(selectControl);
        });
    };

    adhocracy.geo.loadOverviewMap = function (openlayers_url, initialInstances) {
        $.getScript(openlayers_url, function () {
            var map = adhocracy.geo.createMap();

            var bounds = adhocracy.geo.FALLBACK_BOUNDS;

            map.addControls(adhocracy.geo.createControls(false, false));
            map.addLayers(adhocracy.geo.createBaseLayers());

            //var proposalLayer = adhocracy.geo.createRegionProposalsLayer(instanceKey, initialProposals);
            //map.addLayer(proposalLayer);
            //var popupControl = adhocracy.geo.createPopupControl(map, proposalLayer, adhocracy.geo.buildInstancePopup);
            //map.addControl(popupControl);

            //adhocracy.geo.enableMarker('result_list_marker', proposalLayer, popupControl);

            var overviewLayers = adhocracy.geo.createOverviewLayers();
            map.addLayers(overviewLayers);
            adhocracy.geo.createPopupControl(map, overviewLayers[1], adhocracy.geo.buildInstancePopup);

            if (adhocracy.geo.easteregg) {
                var easterLayer = adhocracy.geo.createEastereggLayer();
                map.addLayer(easterLayer);
                adhocracy.geo.createPopupControl(map, easterLayer, adhocracy.geo.buildEastereggPopup);
            }

            map.zoomToExtent(bounds);
            map.addControl(adhocracy.geo.createSelectControl());
        });
    };

    adhocracy.geo.loadSelectInstanceMap = function (layers, tiles, resultList) {

        function addResizeMapButton(plus) {
            var src = '/images/map_resize_rec_plus.png';
            if (!plus) {
                src = '/images/map_resize_rec_minus.png';
            }
            var img = $('<img>', { src: src,
                                   alt: '+'
                                 });
            $('#resize_map_button').empty();
            $('#resize_map_button').append(img);
        }

        var map, enlargeMap, shrinkMap;

        enlargeMap = function (event) {
            addResizeMapButton(false);
            $('#resize_map_button').click(shrinkMap);
            $('#map_startpage_wrapper').removeClass('map_size_normal');
            $('#map_startpage_wrapper').addClass('map_size_large');
            map.updateSize();
        };

        shrinkMap = function (event) {
            addResizeMapButton(true);
            $('#resize_map_button').click(enlargeMap);
            $('#map_startpage_wrapper').addClass('map_size_normal');
            $('#map_startpage_wrapper').removeClass('map_size_large');
            map.updateSize();
        };

        map = adhocracy.geo.createMap();
        var bounds = adhocracy.geo.FALLBACK_BOUNDS;

        map.addControls(adhocracy.geo.createControls(true, false));
        map.addLayers(adhocracy.geo.createBaseLayers());

        var foldLayers = adhocracy.geo.addMultiBoundaryLayer(map, layers, tiles);
        // var foldLayers = null;
        var townHallLayer = adhocracy.geo.addUntiledTownhallLayer(map, resultList);

        var selectControl = adhocracy.geo.createSelectControl();
        map.addControl(selectControl);

        map.zoomToExtent(bounds);

        addResizeMapButton(true);
        $('#resize_map_button').click(enlargeMap);

        var result = {map: map,
                      foldLayers: foldLayers,
                      townHallLayer: townHallLayer,
                      selectControl: selectControl};

        return result;
    };

    adhocracy.geo.instanceSearch = function (state, resultList) {

        var map = state.map;
    //    var foldLayers = state.foldLayers;
        var townHallLayer = state.townHallLayer;
        var selectControl = state.selectControl;

        var max_rows = 3;
        var offset = 0;

        function makeRegionNameElements(item) {
            var text = item.label;
            var text2 = "";
            var is_in = item.is_in;
            while (is_in !== undefined) {
                text2 = is_in.name;
                is_in = is_in.is_in;
            }
            if (text2 != "") {
                text = text + ", " + text2;
            }
            if (item.instance_id != "") {
                return $('<a>', {
                    'class': "link",
                    href: item.url
                }).append(document.createTextNode(text));
            }
            return document.createTextNode(text);
        }

        function makeRegionDetailsElements(item) {
            if (item.instance_id != "") {
                return document.createTextNode(adhocracy.geo.createInstanceDesc(item));
            }
        }

        function instanceEntry(item, numInstance, numRegion) {
            var idBase = 'search_result_list_marker';
            var letterInstance = String.fromCharCode(numInstance + 97);
            var letterRegion = String.fromCharCode(numRegion + 97);
            var li = $('<div/>', {'class': 'search_result'});
            var marker;
            var img;
            if (item.instance_id != "") {
                marker = $('<div>', {'class': 'marker'});
                img = $('<img>', {'class': 'search_result_list_marker marker_' + letterInstance,
                                   src: '/images/map_marker_pink_' + letterInstance + '.png',
                                   id: idBase + '_' + item.region_id,
                                   alt: item.region_id
                                 });
                if (item.authenticated) {
                    marker.addClass('authenticated');
                }
            } else {
                marker = $('<div>', {'class': 'marker_hall' });
                img = $('<img>', {'class': 'search_result_list_marker marker_' + letterRegion,
                                   src: '/images/map_hall_pink_' + letterRegion + '.png',
                                   id: idBase + '_' + item.region_id,
                                   alt: item.region_id
                                 });
            }
            var div = $('<div>', {'class': 'search_result_title'});
            var text;
            var details;

            text = makeRegionNameElements(item);
            details = makeRegionDetailsElements(item);

            marker.append(img);
            li.append(marker);
            li.append(div);
            div.append(text);
            if (item.instance_id != "") {
                li.append(details);
            }
            li.appendTo('#log');

            $("#log").scrollTop(0);
        }

        function resetSearchField(inputValue, count) {
            $('#log').empty();
            $('#search_buttons').empty();
            $('#num_search_result').empty();
            var text = LANG.num_search_result_start_text
                        + ' \"' + inputValue + '\" '
                        + LANG.num_search_result_end_text
                        + ' ' + count + ' ';
            if (count === 1) {
                text = text + LANG.hit_text;
            } else {
                text = text + LANG.hits_text;
            }
            text = text + '.';
            var resultText = document.createTextNode(text);
            $('#num_search_result').append(resultText);
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
                $.map(old, remove);
            }
            if (adhocracy.geo.popup) {
                map.removePopup(adhocracy.geo.popup);
                adhocracy.geo.popup = null;
            }
        }

        function addMarkers(request_term) {
            var len = resultList[request_term].length;
            var num = (offset + max_rows) > len ? len : offset + max_rows;
            var i;
            for (i = offset; i < num; i++) {
                var admin_center = resultList[request_term][i].admin_center;
                if (admin_center) {
                    townHallLayer.addFeatures([admin_center]);
                }
            }
        }

        function fillSearchField(inputValue) {
            //insert result into list
            var count = resultList[inputValue].length;
            var numInstance = 0, numRegion = 0;
            var i;

            resetSearchField(inputValue, count);
            addMarkers(inputValue);

            for (i = offset; i < offset + max_rows && i < count; ++i) {
                instanceEntry(resultList[inputValue][i], numInstance, numRegion);
                if (resultList[inputValue][i].instance_id != "") {
                    numInstance = numInstance + 1;
                } else {
                    numRegion = numRegion + 1;
                }
            }
            adhocracy.geo.enableMarker('search_result_list_marker', townHallLayer, selectControl);

            if (count > max_rows) {
                if (offset + max_rows > max_rows) {
                    var prevButton = $('<div />', {'class': 'button_small', id: 'search_prev'});
                    var prevText = document.createTextNode(LANG.prev_text);
                    prevButton.append(prevText);
                    prevButton.appendTo('#search_buttons');
                    prevButton.click(function (event) {
                        removePreviousMarkers(inputValue);
                        offset = offset - max_rows;
                        fillSearchField(inputValue);
                    });
                }
                var lastPage = Math.min(offset + max_rows, count);
                var pageText = document.createTextNode((offset + 1) + ' '
                                + LANG.to_text + ' ' + lastPage);
                $('#search_buttons').append(pageText);
                if (offset + max_rows < count) {
                    var nextButton = $('<div />', {'class': 'button_small', id: 'search_next'});
                    var nextText = document.createTextNode(LANG.next_text);
                    nextButton.append(nextText);
                    nextButton.appendTo('#search_buttons');
                    nextButton.click(function (event) {
                        removePreviousMarkers(inputValue);
                        offset = offset + max_rows;
                        fillSearchField(inputValue);
                    });
                }
            } else {
                $('#search_next').remove();
                $('#search_prev').remove();
            }
        }

        function buildResultList() {
            var frame = $('<div/>', {
                    'class': 'ui-widget',
                    id: 'search_result_content'
                });

            var heading = $('<h4>');
            var text = document.createTextNode(LANG.search_result_text);
            heading.append(text);

            var infoText = $('<div/>', {id: 'num_search_result'});
            var list = $('<div/>', {id: 'log'});
            var buttons = $('<div>', {id: 'search_buttons'});

            $('#instance_search').append(frame);
            frame.append(heading);
            frame.append(infoText);
            frame.append(list);
            frame.append(buttons);
        }

        var doAutocompletion = true;
        var currentSearch;

        var search_field = $("#overview_search_field");
        var search_button = $("#overview_search_button");

        function querySearchResult() {

            doAutocompletion = false;
            var request_term = search_field.val();

            function makeResponse(item_tuple) {

                /* broken */

                var item = item_tuple[1];
                item.instance_id = item_tuple[0];

                var feature;
                var features = new OpenLayers.Format.GeoJSON({}).read(item.admin_center);
                if (features != null && features.length > 0) {
                    feature = features[0];
                }

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
                };
            }

            function showSearchResult() {
                search_field.autocomplete("close");
                removePreviousMarkers(adhocracy.geo.prevInputValue);
                offset = 0;
                adhocracy.geo.prevInputValue = adhocracy.geo.inputValue;
                adhocracy.geo.inputValue = search_field.val();

                if (resultList[adhocracy.geo.inputValue]) {
                    if ($('#instance_search').children().size() === 1) {
                        buildResultList();
                    }

                    fillSearchField(adhocracy.geo.inputValue);
                    var bounds = new OpenLayers.Bounds();
                    var found = false;
                    var i;
                    for (i = 0; i < resultList[adhocracy.geo.inputValue].length; i++) {
                        var hit = resultList[adhocracy.geo.inputValue][i];
                        //if (hit.instance_id != "") {
                        var bbox = JSON.parse(hit.bbox);
                        var hitBounds = new OpenLayers.Bounds.fromArray(bbox);
                        bounds.extend(hitBounds);
                        found = true;
                        //}
                    }
                    if (found) {
                        map.zoomToExtent(bounds);
                    }
                    //delete resultList[adhocracy.geo.inputValue];
                }
            }

            function errorResponse(xhr, err) {
                currentSearch = undefined;
                search_field.removeClass('ui-autocomplete-loading');
                doAutocompletion = true;
                // console.log('No response from server. URL: ' + url + ', Error: '+err);
            }

            function successResponse(data) {
                search_field.removeClass('ui-autocomplete-loading');
                doAutocompletion = true;
                resultList[request_term] = $.map(data.regions, makeResponse);
                currentSearch = undefined;
                showSearchResult();
            }

            if (!currentSearch || currentSearch !== request_term) {
                currentSearch = request_term;
                if (request_term.length > 2) {
                    search_field.autocomplete("close");
                    $.ajax({
                        beforeSend: function (jqXHR, settings) {
                            search_field.addClass('ui-autocomplete-loading');
                            return true;
                        },
                        url: 'find_instances.json',
                        dataType: "json",
                        data: {
                            query: request_term
                        },
                        success: successResponse,
                        error: errorResponse
                    });
                }
            }
        }


        search_field.keypress(function (event) {
            if (event.which === 13 || event.which === 10) {
                querySearchResult();
            }
        });

        search_button.click(querySearchResult);

        search_field.autocomplete({
            search: function (event, ui) {
                if (!doAutocompletion) {
                    return false;
                }
            },
            source: function (request, response) {
                $.ajax({
                    url: "/autocomplete_instances.json",
                    dataType: "json",
                    data: {
                        query: request.term
                    },
                    success: function (data) {
                        if (doAutocompletion) {
                            var instances = data.instances;
                            var regions = data.regions;
                            // TODO: Put instances and regions in separate
                            // optgroups
                            response(['INSTANCES'].concat(instances, ['REGIONS'], regions));
                        }
                    }
                });
            },
            minLength: 3
        });
    };

    adhocracy.geo.loadSelectInstance = function (openlayers_url) {
        $.getScript(openlayers_url, function () {
            var layers = [];
            var tiles = [];
            var resultList = [];
            var state = adhocracy.geo.loadSelectInstanceMap(layers, tiles, resultList);
            adhocracy.geo.instanceSearch(state, resultList);
        });
    };

    adhocracy.geo.editGeotagInNewProposalWizard = function (openlayers_url, instanceKey) {

        var noPositionClicked, addPositionClicked, addGeoTagHandler, noGeoTagHandler;

        noPositionClicked = function () {
            $('<a>', {
                id: 'create_geo_button',
                'class': 'button_small',
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
        };

        addPositionClicked = function (position) {

            $('<a>', {
                id: 'no_geo_button',
                'class': 'button_small',
                click: noGeoTagHandler
            }).append(document.createTextNode(LANG.no_position_text)).appendTo('#map_div');
            $('<a/>').appendTo('#map_div');

            $('<div />', {
                id: 'map',
                'class': 'edit_map'
            }).appendTo('#map_div');

            adhocracy.geo.loadSingleProposalMap(openlayers_url, instanceKey, null, true, position);

            $('#create_geo_button').remove();

            $('<div />', {
                id: 'attribution_div',
                'class': 'note_map'
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
        };

        addGeoTagHandler = function (event) {
            event.preventDefault();
            addPositionClicked(null);
        };

        noGeoTagHandler = function (event) {
            event.preventDefault();
            noPositionClicked();
        };

        function reloadNewProposalForm() {
            var position = $('#proposal_geotag_field').val();
            if (position != null && position != '') {
                addPositionClicked(position);
            }
        }

        $('#create_geo_button').click(addGeoTagHandler);
        $('#create_geo_button').ready(reloadNewProposalForm);
    };

}());
