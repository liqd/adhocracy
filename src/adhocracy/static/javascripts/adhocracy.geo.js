/*jslint browser: true, vars: true, plusplus: true */
/*global $: true, OpenLayers: true, ko: true */


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

// Make sure we have an "adhocracy" namespace.
var adhocracy = adhocracy || {};

(function () {

    "use strict";

    /***************************************************
     * @namespace: adhocracy.geo
     ***************************************************/

    adhocracy.namespace('adhocracy.geo');

    adhocracy.geo.AVAILABLE_RESOLUTIONS = [
        156543.03390625, 78271.516953125, 39135.7584765625,
        19567.87923828125, 9783.939619140625, 4891.9698095703125,
        2445.9849047851562, 1222.9924523925781, 611.4962261962891,
        305.74811309814453, 152.87405654907226, 76.43702827453613,
        38.218514137268066, 19.109257068634033, 9.554628534317017,
        4.777314267158508, 2.388657133579254, 1.194328566789627,
        0.5971642833948135, 0.29858214169740677, 0.14929107084870338,
        0.07464553542435169
    ];

    adhocracy.geo.layersWithPopup = [];

    adhocracy.geo.inputValue = "";

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

    adhocracy.geo.pagePolygonDefault = {
        strokeColor: "#4D4D4D",
        fillColor: "${fillColor}",
        graphicZIndex: "${zIndex}",
        strokeWidth: 0.5
    };
    adhocracy.geo.pagePolygonSelect = {
        strokeColor: "#111111",
        fillColor: "#343434",
        graphicZIndex: "${zIndex}",
    };

    adhocracy.geo.pagePolygonStyleMap = new OpenLayers.StyleMap({
        'default': new OpenLayers.Style(adhocracy.geo.pagePolygonDefault),
        'select': new OpenLayers.Style(adhocracy.geo.pagePolygonSelect)
    });

    adhocracy.geo.proposalStyleMap = new OpenLayers.StyleMap({
        'default': new OpenLayers.Style(adhocracy.geo.styleProps),
        'select': new OpenLayers.Style(adhocracy.geo.styleSelect)
    });

    adhocracy.geo.createProposalLayer = function () {

        return new OpenLayers.Layer.Vector("proposal", {
            displayInLayerSwitcher: false,
            styleMap: adhocracy.geo.proposalStyleMap
        });
    };

    adhocracy.geo.createPageLayer = function () {

        return new OpenLayers.Layer.Vector("page", {
            displayInLayerSwitcher: false,
            styleMap: adhocracy.geo.pagePolygonStyleMap
        });
    };

    adhocracy.geo.fetchSingleDelegateable = function (objectType, delegateableId, edit, callback) {
        var url = '/' + objectType + '/' + delegateableId + '/get_geotag';
        $.ajax({
            url: url,
            success: function (data) {
                var features = new OpenLayers.Format.GeoJSON({}).read(data);
                if (features) {
                    // assert(features.length==1);
                    var feature = features[0];
                    if (edit) {
                        $('#' + objectType + '_geotag_field').val(new OpenLayers.Format.GeoJSON({}).write(feature));
                    }
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

    adhocracy.geo.townHallSymbolizerDefault = {
        externalGraphic: '/images/townhall-64-grey.png',
        graphicHeight: 15,
        graphicWidth: 12,
        graphicYOffset: -15,
        graphicZIndex: 100
    };

    adhocracy.geo.townHallSymbolizerAuthenticated = {
        externalGraphic: '/images/townhall-64-green.png',
        graphicHeight: 15,
        graphicWidth: 12,
        graphicYOffset: -15,
        graphicZIndex: 150
    };

    adhocracy.geo.townHallSymbolizerInSearch = {
        externalGraphic: '/images/townhall-64-red.png',
        graphicHeight: 30,
        graphicWidth: 24,
        graphicYOffset: -30,
        graphicZIndex: 300,
        backgroundGraphicZIndex: 900
    };

    adhocracy.geo.makeTownHallSymbolizerInSearch = function (letter) {
        return {
            externalGraphic: '/images/townhall-64-red-' + letter + '.png',
            graphicHeight: 30,
            graphicWidth: 24,
            graphicYOffset: -30,
            graphicZIndex: 350,
            backgroundGraphicZIndex: 900
        };
    };

    adhocracy.geo.setBalloonSymbolizer = function (scope, idx) {
        var letter = String.fromCharCode(idx + 97);
        scope.symbolizer = adhocracy.geo.balloonSymbolizer;
        scope.symbolizer.externalGraphic = '/images/map_marker_pink_' + letter + '.png';
        return letter;
    };

    adhocracy.geo.setTownHallSymbolizer = function (scope, idx) {
        scope.symbolizer = adhocracy.geo.townHallSymbolizerDefault;
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
        });
    };

    adhocracy.geo.createAjaxFeatureLayer = function (layerName, url, styleMap, featuresAddedCallback) {

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
        return new OpenLayers.Layer.Vector(layerName, {
            strategies: [new OpenLayers.Strategy.Fixed()],
            protocol: new OpenLayers.Protocol.HTTP({
                url: url,
                format: format
            }),
            styleMap: styleMap,
            rendererOptions: {
                zIndexing: true
            }
        });

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

        var url = '/instance/' + instanceKey + '/get_proposal_geotags';

        var styleMap = new OpenLayers.StyleMap({
                'default': new OpenLayers.Style(adhocracy.geo.styleProps, {
                    rules: [rule, new OpenLayers.Rule({ elseFilter: true })]
                }),
                'select': new OpenLayers.Style(adhocracy.geo.styleSelect)
            });


        var layer = adhocracy.geo.createAjaxFeatureLayer('Proposals', url, styleMap, featuresAddedCallback);

        layer.events.on({
            'featuresadded': featuresAddedCallback
        });

        return layer;
    };

    adhocracy.geo.createRegionPagesLayer = function (instanceKey, initialPages, featuresAddedCallback) {

        var url = '/instance/' + instanceKey + '/get_page_geotags';

        var layer = adhocracy.geo.createAjaxFeatureLayer('Pages', url,
                                                        adhocracy.geo.pagePolygonStyleMap,
                                                        featuresAddedCallback);

        layer.events.on({
            'featuresadded': featuresAddedCallback
        });

        return layer;
    };

    adhocracy.geo.createPageProposalsLayer = function (instanceKey, pageId, featuresAddedCallback) {

        // TODO: Add marker and link them to variant list bidirectionally
        /*
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
        var rules = [rule, new OpenLayers.Rule({ elseFilter: true })];
        */

        var url = '/page/' + pageId + '/proposal_geotags';
        var layer = adhocracy.geo.createAjaxFeatureLayer('proposal', url,
                                                         adhocracy.geo.proposalStyleMap,
                                                         featuresAddedCallback);

        layer.events.on({
            'featuresadded': featuresAddedCallback
        });

        return layer;
    };

    adhocracy.geo.popup = null;

    adhocracy.geo.createPopupControl = function (map, layer, buildPopupContent) {

        var anchor;

        /*
        // this would create a popup offset. it's disabled because it makes
        // the popup open always in the same direction
        OpenLayers.Popup.FramedCloud.prototype.fixedRelativePosition = true;
        OpenLayers.Popup.FramedCloud.prototype.relativePosition = "tr";
        anchor = {'size': new OpenLayers.Size(5, 0), 'offset': new OpenLayers.Pixel(10, 0)};
        */

        anchor = null;

        var closePopup = function (event) {
            if (adhocracy.geo.popup) {
                map.removePopup(adhocracy.geo.popup);
                adhocracy.geo.popup = null;
            }
        };

        var openPopup = function (event) {
            adhocracy.geo.popup = new OpenLayers.Popup.FramedCloud("singlepopup",
                event.feature.geometry.getBounds().getCenterLonLat(),
                null,
                buildPopupContent(event.feature.attributes),
                anchor,
                true,
                closePopup);
            map.addPopup(adhocracy.geo.popup);
        };

        layer.events.on({
            'featureselected': openPopup,
            'featureunselected': closePopup
        });

        adhocracy.geo.layersWithPopup.push(layer);

    };

    adhocracy.geo.addOleControls = function (map) {
        var editor = new OpenLayers.Editor(map, {
            activeControls: ['Navigation', 'SnappingSettings', 'Separator', 'DeleteFeature', 'DragFeature', 'SelectFeature', 'Separator', 'DrawHole', 'ModifyFeature', 'Separator'],
            //featureTypes: ['polygon', 'path', 'point']
            featureTypes: ['polygon']
        });
        editor.startEditMode();

        return editor;

    };

    adhocracy.geo.addEditControls = function (map, layer) {

        var buttonState;
        var pointClicked, addChangeRemoveGeoButton, addAddGeoButton;

        var pointControl = new OpenLayers.Control.DrawFeature(layer, OpenLayers.Handler.Point, {
            featureAdded: function (feature) {
                pointClicked();
            }
        });

        var geotag_field = $('#geotag_field');

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
                text: $.i18n._('set_position')
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
                text: $.i18n._('set_different_position')
            }).appendTo('#edit_map_buttons');

            $('<a />', {
                id: 'remove_geo_button',
                'class': 'button',
                click: function () {
                    layer.removeAllFeatures();
                    geotag_field.val('');
                    updateEditButtons();
                },
                text: $.i18n._('remove_position')
            }).appendTo('#edit_map_buttons');
        };

        function updateGeotagField() {
            var transformed_feature = layer.features[0].clone();
            geotag_field.val(new OpenLayers.Format.GeoJSON({}).write(transformed_feature));
            map.setCenter(layer.features[0].geometry.getBounds().getCenterLonLat(),
                map.getZoom());
        }

        pointClicked = function () {
            pointControl.deactivate();
            updateEditButtons();
            updateGeotagField();
        };

        function featureFetched(feature) {
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

        return featureFetched;
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
            if (layer.features[i].attributes.regionId === feature.attributes.regionId) {
                return true;
            }
        }
        return false;
    };

    adhocracy.geo.buildInstancePopup = function (attributes) {
        // attributes are the feature attributes
        
        var imageUrl, authLabel, numProposalsLabel, numMembersLabel;

        if (attributes.iconUrl) {
            if (attributes.isAuthenticated) {
                // iconUrl attribute is set in search results
                imageUrl = attributes.iconUrl;
                authLabel = ' \u00B7 ' + $.i18n._('authenticated_instance');
            } else {
                imageUrl = attributes.iconUrl;
                authLabel = '';
            }
        } else {
            if (attributes.isAuthenticated) {
                imageUrl = '/images/townhall-64-green.png';
                authLabel = ' \u00B7 ' + $.i18n._('authenticated_instance');
            } else {
                imageUrl = '/images/townhall-64-grey.png';
                authLabel = '';
            }
        }
        if (attributes.numProposals === 1) {
            numProposalsLabel = $.i18n._('proposal');
        } else {
            numProposalsLabel = $.i18n._('proposals');
        }
        if (attributes.numMembers === 1) {
            numMembersLabel = $.i18n._('member');
        } else {
            numMembersLabel = $.i18n._('members');
        }

        return "<div class='instance_popup_wrapper'><div class='instance_popup_image'>" +
            "<img src='" + imageUrl + "' /></div>" +
            "<a class='instance_popup_title' href='" + attributes.url + "'>" +
            attributes.label + "</a>" +
            "<div class='meta'>" +
            attributes.numProposals + ' ' + numProposalsLabel + ' \u00B7 ' +
            attributes.numMembers + ' ' + numMembersLabel +
            authLabel + "</div></div></div>";
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

    adhocracy.geo.getLayerIndex = function (adminLevel) {
        return adhocracy.geo.adminLevels.indexOf(adminLevel);
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
                    var url = '/get_admin_centres.json' +
                        '?x=' + newTiles[i].x +
                        '&y=' + newTiles[i].y +
                        '&zoom=' + map.getZoom() +
                        '&adminLevel=' + adminLevel;
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
            return (searchEntry.regionId === feature.attributes.regionId &&
                    searchEntry.instanceId !== "");
        }

        function isRegion(feature, searchEntry) {
            return (searchEntry.regionId === feature.attributes.regionId &&
                    searchEntry.instanceId === "");
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
                        if (result[i].instanceId === "") {
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
                        if (result[i].instanceId !== "") {
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
            var adminLevel = feature.attributes.adminLevel;
            var layerIdx = adhocracy.geo.getLayerIndex(adminLevel);
            var style = adhocracy.geo.displayMap[zoom]['styles'][layerIdx];
            return (style === 0);
        }

        var rule = new OpenLayers.Rule({symbolizer: adhocracy.geo.balloonSymbolizer});
        rule.evaluate = filterInstancesBalloon;
        var rule2 = new OpenLayers.Rule({ symbolizer: adhocracy.geo.styleTransparentProps });
        rule2.evaluate = filterInstancesInVisible;
        var rule3 = new OpenLayers.Rule({elseFilter: true, symbolizer: adhocracy.geo.townHallSymbolizerDefault});
        rule3.evaluate = filterElse;

        townHallLayer.styleMap = new OpenLayers.Style(adhocracy.geo.styleProps, {rules: [rule, rule2, rule3]});
        townHallLayer.moveTo = moveTownHallTo;
        map.addLayer(townHallLayer);
        adhocracy.geo.createPopupControl(map, townHallLayer, adhocracy.geo.buildInstancePopup);

        return townHallLayer;
    };

    adhocracy.geo.addMultiBoundaryLayer = function (map, layers, tiles) {

        function isValidAdminLevel(adminLevel) {
            var i = 0;
            for (i = 0; i < adhocracy.geo.adminLevels.length; i++) {
                if (adhocracy.geo.adminLevels[i] === adminLevel) {
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
            if (zoom !== null && zoomChanged !== null) {
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
                                    layers[i][k].styleMap['default'] =
                                        new OpenLayers.Style(adhocracy.geo.styleBorder);
                                    layers[i][k].styleMap['default'] =
                                        new OpenLayers.Style(adhocracy.geo.styleBorder);
                                    redrawFeatures(layers[i][k], adhocracy.geo.styleBorder);
                                }
                            } else {
                                for (k = 0; k < adhocracy.geo.displayMap.length; k++) {
                                    layers[i][k].styleMap['default'] =
                                        new OpenLayers.Style(adhocracy.geo.styleArea);
                                    layers[i][k].styleMap['default'] =
                                        new OpenLayers.Style(adhocracy.geo.styleArea);
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
                        var adminLevel = parseInt(feature.attributes.adminLevel, 10);
                        var zoom2 = parseInt(feature.attributes.zoom, 10);
                        if (zoom2 >= 0 && zoom2 < 15 && isValidAdminLevel(adminLevel)) {
                            layers[adhocracy.geo.getLayerIndex(adminLevel)][zoom2].addFeatures([feature]);
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
                        var url = '/get_tiled_boundaries.json' +
                            '?x=' + newTiles[i].x +
                            '&y=' + newTiles[i].y +
                            '&zoom=' + zoom +
                            '&adminLevel=' + adhocracy.geo.adminLevels[this.layersIdx];
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

                layers[layersIdx][z] = new OpenLayers.Layer.Vector(layername, {
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


    /**
     * minZoomLevel, maxZoomLevel: value between 0 and 19.
     */
    adhocracy.geo.createBaseLayers = function (p, min_zoom_level, max_zoom_level, admin_boundaries, blank) {
        var p = $.extend({
            'imageLayers': [],
        }, p);

        var osmOptions = {
            displayInLayerSwitcher: true,
            zoomOffset: min_zoom_level,
            numZoomLevels: max_zoom_level - min_zoom_level,
            maxResolution: adhocracy.geo.AVAILABLE_RESOLUTIONS[min_zoom_level],
            tileOptions: {crossOriginKeyword: null},
        };
        var osmOptionsOverlay = $.extend({isBaseLayer: false}, osmOptions);

        var admin_boundary_layer = new OpenLayers.Layer.OSM("OSM Admin Boundaries",
            "http://129.206.74.245:8007/tms_b.ashx?x=${x}&y=${y}&z=${z}", osmOptionsOverlay);

        var baseLayers = [
            // top definition is selected if setBaseLayer isn't called
            // default Openstreetmap Baselayer
            new OpenLayers.Layer.OSM("Open Street Map", "", osmOptions),
            new OpenLayers.Layer.OSM("OSM Roads Greyscale",
                        "http://129.206.74.245:8008/tms_rg.ashx?x=${x}&y=${y}&z=${z}", osmOptions),
            new OpenLayers.Layer.OSM("Public Transport",
                        "http://a.tile2.opencyclemap.org/transport/${z}/${x}/${y}.png", osmOptions),
            new OpenLayers.Layer.OSM("Transport Map",
                        "http://otile1.mqcdn.com/tiles/1.0.0./osm/${z}/${x}/${y}.png", osmOptions),
            new OpenLayers.Layer.OSM("&Ouml;pnv Deutschland",
                        "http://tile.xn--pnvkarte-m4a.de/tilegen/${z}/${x}/${y}.png", osmOptions),
            admin_boundary_layer
        ];
        
        var i = 0;
        for (i = 0; i < p.imageLayers.length; i++) {
            var l = p.imageLayers[i];
            baseLayers.push(new OpenLayers.Layer.Image(
                l.title,
                l.url,
                new OpenLayers.Bounds(l.bounds),
                new OpenLayers.Size(l.size),
                $.extend({'visibility': l.visible}, osmOptionsOverlay)));
        };

        if (!admin_boundaries) {
            admin_boundary_layer.setVisibility(false);
        }

        // Blank Baselayer
        if (blank) {
            baseLayers.push(new OpenLayers.Layer("Blank", {isBaseLayer: true}));
        }

        return baseLayers;
    };


    adhocracy.geo.createMap = function (p) {

        adhocracy.geo.FALLBACK_BOUNDS = new OpenLayers.Bounds(p.fallbackBounds);

        var map = new OpenLayers.Map('map', {
            restrictedExtent: new OpenLayers.Bounds(p.restrictedBounds),
            projection: "EPSG:900913",
            controls: []
        });


        /* set map viewport restrictions which are respected in
         * `zoomToRestrictedExtent`.
         *
         * the 4 parameters represent the margin between real and restricted
         * viewport
         * */
        map.setRestrictedExtent = function (rleft, rbottom, rright, rtop) {
            map.rleft = rleft;
            map.rbottom = rbottom;
            map.rright = rright;
            map.rtop = rtop;
        };

        map.zoomToRestrictedExtent = function (bounds) {
        /* variation of zoomToExtent which takes a custom viewport into account
         * which has been set by `setRestrictedExtent`.
         *
         * TODO: document correctness proof of formulas below
         */

            var size = map.getSize();

            var rx1 = (map.rleft || 0) / size.w;
            var ry1 = (map.rbottom || 0) / size.h;
            var rx2 = 1 - ((map.rright || 0) / size.w);
            var ry2 = 1 - ((map.rtop || 0) / size.h);

            var x1 = bounds.left;
            var y1 = bounds.bottom;
            var x2 = bounds.right;
            var y2 = bounds.top;

            var sx1 = ((x1 * rx2) - (x2 * rx1)) / (rx2 - rx1);
            var sy1 = ((y1 * ry2) - (y2 * ry1)) / (ry2 - ry1);
            var sx2 = ((rx2 - 1) * x1 + (1 - rx1) * x2) / (rx2 - rx1);
            var sy2 = ((ry2 - 1) * y1 + (1 - ry1) * y2) / (ry2 - ry1);

            map.zoomToExtent(new OpenLayers.Bounds(sx1, sy1, sx2, sy2));
        };

        return map;
    };


    adhocracy.geo.createControls = function (fullControls, keyboardControls) {

        var mapControls = [
            new OpenLayers.Control.Navigation({'handleRightClicks': true}),
            new OpenLayers.Control.ScaleLine({'geodesic': true})
        ];

        if (fullControls) {
            mapControls.push(new OpenLayers.Control.PanZoomBar());
            mapControls.push(new OpenLayers.Control.LayerSwitcher());
            // mapControls.push(new OpenLayers.Control.Scale());
        } else {
            mapControls.push(new OpenLayers.Control.ZoomPanel());
        }
        if (keyboardControls) {
            // use KeyboardDefault only when map is the central element
            mapControls.push(new OpenLayers.Control.KeyboardDefaults());
        }

        return mapControls;
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
        result = result + "<a href='/proposal/" + attributes.regionId + "'>" + title + "</a>";
        result = result + "<div class='meta'>";
        result = result + attributes.num_for + ":" + attributes.num_against + " " + $.i18n._('votes');
        result = result + "</div>";
        result = result + "</div>";
        return result;
    };

    adhocracy.geo.buildPagePopup = function (attributes) {
        var maxPopupTitleLength = 30;
        var title = attributes.title;
        if (title.length > maxPopupTitleLength) {
            title = title.substring(0, maxPopupTitleLength) + " ...";
        }

        var numProposalsLabel;
        if (attributes.numProposals === 1) {
            numProposalsLabel = $.i18n._('proposal');
        } else {
            numProposalsLabel = $.i18n._('proposals');
        }

        var result = "<div class='page_popup_title'>";
        result = result + "<a href='" + attributes.url + "'>" + title + "</a>";
        result = result + "<div class='meta'>";
        result = result + attributes.numProposals + ' ' + numProposalsLabel;
        result = result + "</div>";
        result = result + "</div>";
        result = result + "<a href='/proposal/new?page=" + attributes.id + "'> " + $.i18n._('new_proposal') + "</a>";
        return result;
    };


    adhocracy.geo.buildEastereggPopup = function (attributes) {
        return "<div class='easteregg_popup_title'><img src='" + attributes.img + "'><br>" + attributes.text + "</div>";
    };


    adhocracy.geo.createSelectControl = function () {

        var selectControl = new OpenLayers.Control.SelectFeature(adhocracy.geo.layersWithPopup, {
                clickout: true,
                toggle: true,
                multiple: false,
                hover: false,
                box: false,
                autoActivate: true
            });

        return selectControl;
    };

    adhocracy.geo.loadPageMap = function (p) {
        var p = $.extend({
            'edit': false,
        }, p);
        var map = adhocracy.geo.createMap(p);

        var waiter = adhocracy.geo.createWaiter(3, function (bounds) {
            map.zoomToExtent(bounds);
        });

        map.addControls(adhocracy.geo.createControls(p.edit, false));
        map.addLayers(adhocracy.geo.createBaseLayers(p, 5, 19));
        var regionBoundaryLayers = adhocracy.geo.createRegionBoundaryLayer(p.instanceKey, function (feature) {
            waiter(feature, true);
        });
        map.addLayers(regionBoundaryLayers);
        //adhocracy.geo.createPopupControl(map, regionBoundaryLayers[1], adhocracy.geo.buildInstancePopup);

        var proposalLayer = adhocracy.geo.createPageProposalsLayer(p.instanceKey, p.pageId, function (features) {
            waiter(features, true);
        });
        map.addLayer(proposalLayer);
        adhocracy.geo.createPopupControl(map, proposalLayer, adhocracy.geo.buildProposalPopup);


        adhocracy.geo.fetchSingleDelegateable('page', p.pageId, p.edit, function (feature) {
            if (p.edit) {
                var editor = adhocracy.geo.addOleControls(map);
                if (feature) {
                    editor.loadFeatures([feature]);
                }
                $('form#edit_geotag').on('submit', function (event) {
                    //$('#geotag_field').val(new OpenLayers.Format.GeoJSON({}).write(editor.toMultiPolygon(editor.editLayer.features)));
                    if (editor.editLayer.features.length > 0) {
                        $('#geotag_field').val(new OpenLayers.Format.GeoJSON({}).write(editor.editLayer.features[0]));
                    } else {
                        $('#geotag_field').val(new OpenLayers.Format.GeoJSON({}).write(''));
                    }
                    editor.stopEditMode();
                    return true;
                });
            } else {
                var pageLayer = adhocracy.geo.createPageLayer();
                map.addLayer(pageLayer);
                map.setLayerIndex(pageLayer, 500);
                map.setLayerIndex(proposalLayer, 550);
                pageLayer.addFeatures([feature]);
                adhocracy.geo.createPopupControl(map, pageLayer, adhocracy.geo.buildPagePopup);

                map.addControl(adhocracy.geo.createSelectControl());
            }

            waiter(feature, true);
        });
    };

    adhocracy.geo.loadSingleProposalMap = function (p) {
        var p = $.extend({
            'edit': false,
            'position': null
        }, p);

        var map = adhocracy.geo.createMap(p);

        var numFetches = 1;
        if (p.proposalId) {
            numFetches = 2;
        }
        var waiter = adhocracy.geo.createWaiter(numFetches, function (bounds) {
            map.zoomToExtent(bounds);
        });

        map.addControls(adhocracy.geo.createControls(p.edit, false));
        map.addLayers(adhocracy.geo.createBaseLayers(p, 5, 19));
        var regionBoundaryLayers = adhocracy.geo.createRegionBoundaryLayer(p.instanceKey, function (feature) {
            waiter(feature);
        });
        map.addLayers(regionBoundaryLayers);
        adhocracy.geo.createPopupControl(map, regionBoundaryLayers[1], adhocracy.geo.buildInstancePopup);

        var proposalLayer = adhocracy.geo.createProposalLayer();
        map.addLayer(proposalLayer);
        adhocracy.geo.createPopupControl(map, proposalLayer, adhocracy.geo.buildProposalPopup);

        var singleProposalFetchedCallback;
        if (p.edit) {
            singleProposalFetchedCallback = adhocracy.geo.addEditControls(map, proposalLayer);
        }

        //don't try to fetch proposals geotags when there's no proposal (i.e. if proposal is created)
        if (p.proposalId) {
            adhocracy.geo.fetchSingleDelegateable('proposal', p.proposalId, p.edit, function (feature) {
                if (feature) {
                    proposalLayer.addFeatures([feature]);
                }

                if (p.edit) {
                    singleProposalFetchedCallback(feature);
                }

                waiter(feature);
            });
        } else {
            var feature = null;
            if (p.position) {
                var features = new OpenLayers.Format.GeoJSON({}).read(p.position);
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
    };

    adhocracy.geo.enableMarker = function (id, layer, selectControl) {
        $('.' + id).click(function (event) {
            var target = event.target || event.srcElement;
            var feature = layer.getFeaturesByAttribute('regionId', parseInt(target.id.substring((id + '_').length), 10))[0];
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

    adhocracy.geo.loadRegionMap = function (p) {
        var p = $.extend({
            'initialProposals': [],
            'initialPages': [],
            'largeMap': false,
            'fullRegion': true
        }, p);

        var map;

        if (p.largeMap) {
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

        map = adhocracy.geo.createMap(p);
        adhocracy.geo.map = map;

        var waiter = adhocracy.geo.createWaiter(p.fullRegion ? 1 : 3, function (bounds) {
            map.zoomToExtent(bounds);

            var controls;
            if (p.largeMap) {
                controls = adhocracy.geo.createControls(true, true);
            } else {
                controls = adhocracy.geo.createControls(false, false);
            }
            map.addControls(controls);
        });

        map.addLayers(adhocracy.geo.createBaseLayers(p, 5, 19));
        var regionBoundaryLayers = adhocracy.geo.createRegionBoundaryLayer(p.instanceKey, function (feature) {
            waiter(feature, false);
        });
        map.addLayers(regionBoundaryLayers);
        adhocracy.geo.createPopupControl(map, regionBoundaryLayers[1], adhocracy.geo.buildInstancePopup);

        var proposalLayer = adhocracy.geo.createRegionProposalsLayer(p.instanceKey, p.initialProposals, function (features) {
            if (!(p.fullRegion)) {
                waiter(features, true);
            }
        });
        map.addLayer(proposalLayer);
        var proposalPopupControl = adhocracy.geo.createPopupControl(map, proposalLayer, adhocracy.geo.buildProposalPopup);

        var pageLayer = adhocracy.geo.createRegionPagesLayer(p.instanceKey, p.initialPages, function (features) {
            if (!(p.fullRegion)) {
                waiter(features, true);
            }
        });
        map.addLayer(pageLayer);
        map.setLayerIndex(pageLayer, 500);
        map.setLayerIndex(proposalLayer, 550);
        var pagePopupControl = adhocracy.geo.createPopupControl(map, pageLayer, adhocracy.geo.buildPagePopup);

        if (adhocracy.geo.easteregg) {
            var easterLayer = adhocracy.geo.createEastereggLayer();
            map.addLayer(easterLayer);
            adhocracy.geo.createPopupControl(map, easterLayer, adhocracy.geo.buildEastereggPopup);
        }
        var selectControl = adhocracy.geo.createSelectControl();
        adhocracy.geo.enableMarker('result_list_marker', proposalLayer, selectControl);
        map.addControl(selectControl);
    };

    adhocracy.geo.loadOverviewMap = function (p) {
        var p = $.extend({
            'initialInstances': []
        }, p);
        var map = adhocracy.geo.createMap(p);

        map.addControls(adhocracy.geo.createControls(false, false));
        var baseLayers = adhocracy.geo.createBaseLayers(p, 5, 12);
        map.addLayers(baseLayers);
        map.setBaseLayer(baseLayers[1]);

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
                    var feature = features[i];
                    boundaryLayer.addFeatures([feature]);
                    //callback(feature);
                    if (feature.attributes.admin_center) {
                        var features2 = new OpenLayers.Format.GeoJSON({}).read(feature.attributes.admin_center);
                        var feature2 = features2[0];
                        townHallLayer.addFeatures([feature2]);
                    }
                }
            },
            error: function (xhr, err) {
                //console.log('No response from server, sorry. url: ' + url + ', Error: '+err);
                //alert('No response from server, sorry. Error: '+err);
            }
        });

        map.addLayers([boundaryLayer, townHallLayer]);
        adhocracy.geo.createPopupControl(map, townHallLayer, adhocracy.geo.buildInstancePopup);
        map.addControl(adhocracy.geo.createSelectControl());
        map.zoomToExtent(adhocracy.geo.FALLBACK_BOUNDS);
    };

    adhocracy.geo.addResizeMapButton = function (map, is_fullscreen) {
        var enlargeMap, shrinkMap;

        enlargeMap = function (event) {
            var top = $('#header').outerHeight();
            $('body').css('overflow', 'hidden');
            $('#page_margins').removeClass('page_margins');
            $('#content-top').removeClass('size_normal');
            $('#map_wrapper').removeClass('map_size_normal').addClass('map_size_full').css('top', top + 'px');
            adhocracy.geo.addResizeMapButton(map, true);
            $('#resize_map_button').click(shrinkMap);
            $('#map_startpage_wrapper').removeClass('map_size_normal');
            $('#map_startpage_wrapper').addClass('map_size_large');
            $('#content-startpage').hide();
            $('#content-bottom').hide();
            $('footer').hide();
            map.updateSize();
        };

        shrinkMap = function (event) {
            $('body').css('overflow', 'auto');
            $('#page_margins').addClass('page_margins');
            $('#content-top').addClass('size_normal');
            $('#map_wrapper').removeClass('map_size_full').addClass('map_size_normal').css('top', 'auto');
            adhocracy.geo.addResizeMapButton(map, false);
            $('#resize_map_button').click(enlargeMap);
            $('#map_startpage_wrapper').addClass('map_size_normal');
            $('#map_startpage_wrapper').removeClass('map_size_large');
            $('#content-startpage').show();
            $('#content-bottom').show();
            $('footer').show();
            map.updateSize();
        };

        var src;
        if (is_fullscreen) {
            src = '/images/map_resize_full_exit.png';
        } else {
            src = '/images/map_resize_full.png';
        }
        var img = $('<img>', { src: src,
                               alt: '+'
                             });
        $('#resize_map_button').empty();
        $('#resize_map_button').append(img);
        $('#resize_map_button').click(enlargeMap);
    };

    /**
     * generic object which coordinates
     *  - lists of items which have geotags
     *  - openlayers layers these items are displayed on and associated options
     *
     * on construction the actual list which stores the data can be passed.
     * this is assumed to be a ko.observableArray.
     */
    adhocracy.geo.listModel = function (list) {
        var self = this;

        self.defaultOptions = {
            makeFeature: function (item) {
                return new OpenLayers.Feature.Vector(
                    item.geometry,
                    item.attributes,
                    item.style
                );
            },
            makeFeatureFid: function (item) {
                return item.fid;
            },
            makePopup: function (item) {
            }
        };

        self.registeredLayers = [];

        if (list === undefined) {
            self.items = ko.observableArray();
        } else {
            self.items = list;
        }

        self.addItemToLayer = function (item, options) {
            var feature = options.makeFeature(item);
            options.layer.addFeatures([feature]);
        };

        self.removeItemFromLayer = function (item, options) {
            options.layer.removeFeatures([
                options.layer.getFeatureByFid(options.makeFeatureFid(item))
            ]);
        };

        self.addItem = function (item) {
            self.items.push(item);
            ko.utils.arrayForEach(self.registeredLayers, function (options) {
                self.addItemToLayer(item, options);
            });
        };

        self.removeItem = function (item) {
            ko.utils.arrayForEach(self.registeredLayers, function (options) {
                self.removeItemFromLayer(item, options);
            });
            self.items.remove(item);
        };

        self.removeAll = function () {
            // using reverse loop here in order to not break
            for (var i = self.items().length - 1; i >= 0; i--) {
                self.removeItem(self.items()[i]);
            }
        };

        self.refreshAll = function () {
            ko.utils.arrayForEach(self.registeredLayers, function (options) {
                ko.utils.arrayForEach(self.items(), function (item) {
                    options.layer.drawFeature(options.makeFeature(item));
                });
            });
        };

        self.registerWithMapLayer = function (options) {
            self.registeredLayers.push($.extend(self.defaultOptions, options));
            ko.utils.arrayForEach(self.items(), function (item) {
                self.addItemToLayer(item, options);
            });
        };

        return self;
    };

    adhocracy.geo.instanceSearchModel = function () {
        var self = this;

        self.searchResults = ko.observableArray();
        self.searchQuery = ko.observable();
        self.showSearchResults = ko.observable(false);

        self.itemsPerPage = 10;
        self.visiblePage = ko.observable(0);

        self.numberHits = ko.computed(function () {
            return (self.searchResults().length);
        });
        self.lastPage = ko.computed(function () {
            return Math.floor((self.numberHits() - 1) / self.itemsPerPage);
        });
        self.hasPrevPage = ko.computed(function () {
            return (self.visiblePage() > 0);
        });
        self.hasNextPage = ko.computed(function () {
            return (self.lastPage() > self.visiblePage());
        });
        self.isItemNumberVisible = function (nr) {
            return (Math.floor(nr / self.itemsPerPage) === self.visiblePage());
        };
        self.isVisible = function (item) {
            return self.isItemNumberVisible(self.searchResults().indexOf(item));
        };
        self.positionNrInPage = function (nr) {
            return (nr % self.itemsPerPage);
        };
        self.positionInPage = function (item) {
            return self.positionNrInPage(self.searchResults().indexOf(item));
        };
        self.getLetter = function (item) {
            var position = self.positionInPage(item);
            return String.fromCharCode(position + 97);
        };
        self.updateFeatures = function () {
            adhocracy.geo.searchResultList.refreshAll();
        };
        self.goPrevPage = function () {
            if (self.hasPrevPage) {
                var current = self.visiblePage();
                self.visiblePage(current - 1);
                self.updateFeatures();
            }
        };
        self.goNextPage = function () {
            if (self.hasNextPage) {
                var current = self.visiblePage();
                self.visiblePage(current + 1);
                self.updateFeatures();
            }
        };
    };

    adhocracy.geo.showSelectInstanceMap = function (p) {

        // build base map layers

        var map = adhocracy.geo.createMap(p);

        map.addControls(adhocracy.geo.createControls(true, false));
        var baseLayers = adhocracy.geo.createBaseLayers(p, 5, 12, true);
        map.addLayers(baseLayers);
        map.setBaseLayer(baseLayers[1]);

        // var foldLayers = adhocracy.geo.addMultiBoundaryLayer(map, layers, tiles);

        var townHallLayer =  new OpenLayers.Layer.Vector('instance_townhalls', {
            displayInLayerSwitcher: false
        });

        // var searchResultLayer =  new OpenLayers.Layer.Vector('search_results', {
        //     displayInLayerSwitcher: true
        // });

        // build townhall layer

        map.addLayer(townHallLayer);
        // map.addLayer(searchResultLayer);

        var instanceList = new adhocracy.geo.listModel();

        instanceList.registerWithMapLayer({
            layer: townHallLayer,
            makeFeature: function (item) {
                var geometry = new OpenLayers.Format.GeoJSON().read(item.geometry, "Geometry");
                var style;
                if (item.properties.isAuthenticated) {
                    style = adhocracy.geo.townHallSymbolizerAuthenticated;
                } else {
                    style = adhocracy.geo.townHallSymbolizerDefault;
                }
                return new OpenLayers.Feature.Vector(geometry, item.properties, style);
            }
        });

        $.ajax({
            url: '/instance/get_all_instance_centres.json',
            success: function (data) {
                ko.utils.arrayForEach(data.features, function (item) {
                    instanceList.addItem(item);
                });
            }
        });

        adhocracy.geo.createPopupControl(map, townHallLayer, adhocracy.geo.buildInstancePopup);
        var selectControl = adhocracy.geo.createSelectControl();
        map.addControl(selectControl);


        // zoomcontrol restricts by 26 px from the left;
        var restrictLeft = 26;
        // search box restricts by 250 px from the right;
        var restrictRight = 250;
        map.setRestrictedExtent(restrictLeft, 0, restrictRight, 0);

        map.zoomToRestrictedExtent(adhocracy.geo.FALLBACK_BOUNDS);

        adhocracy.geo.addResizeMapButton(map, false);

        // all the instance search stuff

        // the result list is maintained in adhocracy.geo.instanceSearch
        adhocracy.geo.instanceSearch = new adhocracy.geo.instanceSearchModel();
        ko.applyBindings(adhocracy.geo.instanceSearch);

        // and passed over to the list object which maintains the display on
        // the map
        adhocracy.geo.searchResultList = new adhocracy.geo.listModel(adhocracy.geo.instanceSearch.searchResults);

        adhocracy.geo.searchResultList.registerWithMapLayer({
            layer: townHallLayer,
            makeFeature: function (item) {
                var geometry = item.geoCentre;
                var style = item.featureStyle();
                var attributes = ko.toJS(item);
                var feature = new OpenLayers.Feature.Vector(geometry, attributes, style);
                feature.fid = item.fid;
                item.feature(feature);
                return feature;
            }
        });

        var doAutocompletion = true;
        var search_field = $("#overview_search_field");
        var search_button = $("#overview_search_button");

        adhocracy.geo.searchItemModel = function (raw) {
            var self = this;
            self.fid = raw.id;
            self.label = ko.observable(raw.label);
            self.numProposals = ko.observable(raw.numProposals);
            self.numMembers = ko.observable(raw.numMembers);
            self.url = ko.observable(raw.url);
            self.directHit = ko.observable(raw.directHit);
            self.regionName = ko.observable(raw.regionName);
            self.geoCentre = new OpenLayers.Format.GeoJSON().read(raw.geoCentre, "Geometry");
            self.bbox = new OpenLayers.Bounds(raw.bbox);
            // this is the icon used in search list
            self.letter = ko.computed(function () {
                return adhocracy.geo.instanceSearch.getLetter(self);
            });
            self.iconUrl = ko.computed(function () {
                var letter = self.letter();
                if (self.isAuthenticated) {
                    return '/images/townhall-64-red-' + letter + '.png';
                } else {
                    return '/images/townhall-64-red-' + letter + '.png';
                }
            });
            self.isVisible = ko.computed(function () {
                return adhocracy.geo.instanceSearch.isVisible(self);
            });
            self.featureStyle = ko.computed(function () {
                if (self.isVisible()) {
                    return adhocracy.geo.makeTownHallSymbolizerInSearch(self.letter());
                } else {
                    return adhocracy.geo.townHallSymbolizerInSearch;
                }
            });
            self.feature = ko.observable();
            self.isAuthenticated = ko.observable(raw.isAuthenticated);
            self.togglePopup = function () {
                var feature = self.feature();
                selectControl.clickFeature(feature);
            };
        };

        function querySearchResult() {

            doAutocompletion = false;
            var request_term = search_field.val();

            function errorResponse(xhr, err) {
                search_field.removeClass('ui-autocomplete-loading');
                doAutocompletion = true;
                // console.log('No response from server. URL: ' + url + ', Error: '+err);
            }

            function successResponse(data) {
                search_field.removeClass('ui-autocomplete-loading');
                doAutocompletion = true;

                adhocracy.geo.searchResultList.removeAll();
                adhocracy.geo.instanceSearch.visiblePage(0);
                
                var total_bbox = new OpenLayers.Bounds();
                ko.utils.arrayForEach(data.instances, function (raw) {
                    var item = new adhocracy.geo.searchItemModel(raw);
                    ko.applyBindings(item);
                    adhocracy.geo.searchResultList.addItem(item);
                    total_bbox.extend(item.bbox);
                });

                if (data.instances.length > 0) {
                    map.zoomToRestrictedExtent(total_bbox);
                }

                adhocracy.geo.instanceSearch.searchQuery(data.query_string);
                adhocracy.geo.instanceSearch.showSearchResults(true);

                search_field.autocomplete("close");
            }

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
                            response(data.instances);
                        }
                    }
                });
            },
            select: function (event, ui) {
                querySearchResult();
            },
            minLength: 3
        });
    };


    adhocracy.geo.editGeotagInNewProposalWizard = function (p) {

        var noPositionClicked, addPositionClicked, addGeoTagHandler, noGeoTagHandler;

        noPositionClicked = function () {
            $('<a>', {
                id: 'create_geo_button',
                'class': 'button_small',
                click: addGeoTagHandler
            }).append(document.createTextNode($.i18n._('add_position'))).appendTo('#map_div');
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
            }).append(document.createTextNode($.i18n._('no_position'))).appendTo('#map_div');
            $('<a/>').appendTo('#map_div');

            $('<div />', {
                id: 'map',
                'class': 'proposal_create_map'
            }).appendTo('#map_div');

            adhocracy.geo.loadSingleProposalMap(
                $.extend({
                    'proposalId': null,
                    'edit': true,
                    'position': position
                }, p)
            );

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
            $('#attribution_div').append(document.createTextNode('-' + $.i18n._('osm_cartographer') + '('));
            var license_link = $('<a>', {
                href: 'http://creativecommons.org/licenses/by-sa/2.0/'
            });
            license_link.appendTo('#attribution_div');
            license_link.append(document.createTextNode($.i18n._('license')));
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
            if (position !== null && position !== '') {
                addPositionClicked(position);
            }
        }

        $('#create_geo_button').click(addGeoTagHandler);
        $('#create_geo_button').ready(reloadNewProposalForm);
    };

}());
