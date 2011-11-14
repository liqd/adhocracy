/*jslint vars:true, browser:true, nomen:true */
/*global document:true, jQuery:true, $:true, ko:true */


/**
 * Javascript application code for adhocracy
 *
 * @module adhocracy
 *
 */

// Make sure we have an "adhocracy" namespace.
var adhocracy;
if (typeof (adhocracy) === "undefined") {
    adhocracy = {};
}

(function () {

    "use strict";

    /**
     * @namespace adhocracy
     * @class PaperModel
     */
    adhocracy.PaperModel = function () {
        this.variants = {
            /**
             * Cache for variant data
             *
             * @property cache
             * @type object
             * @protected
             */
            cache: {},
            /**
             * Enable/disable diff display mode. The final decicion if a
             * diff or plain text is shown is made in .showText().
             *
             * @property switchDiff
             * @type bool (observable)
             * @default
             */
            switchDiff: ko.observable(true),
            /**
             * The current
             * @property switchDiff
             * @type object (with observeable properties)
             * @default
             */
            current: undefined,
            init: function (data) {
                var variant = data.variant;
                this.cache[variant] = data;
                this.current = ko.mapping.fromJS(data);
                this.load(variant);
            },
            /**
             * Load data from a certain variant from a url and
             * display it. If the data is in the cache, the
             * url is ignored.
             *
             * @method load
             * @param {String} variant The name of the variant
             * @param {String} url The url to load data from
             * @return {undefined}
             */
            load: function (variant, url, callback) {
                var self = this,
                    update_model;

                update_model = function () {
                    ko.mapping.fromJS(self.cache[variant], self.current);
                };

                if (this.cache[variant] !== undefined) {
                    update_model();
                } else {
                    $.getJSON(url,
                        {variant_json: '1'},
                        function (data) {
                            self.cache[data.variant] = data;
                            update_model();
                            callback();
                        });
                }
            },
            /**
             * Tell if the plain or the diff text should be shown.
             *
             * @method showText
             * @return {String} 'plain' or 'diff'
             */
            showText: function () {
                if (this.current.is_head()) {
                    return 'plain';
                }
                if (this.switchDiff()) {
                    return 'diff';
                }
                return 'plain';
            },
            /**
             * Convenience shortcut to .showText() === 'diff'
             *
             * @method showDiff
             * @return {Boolean}
             */
            showDiff: function () { return this.showText() === 'diff'; },
            /**
             * Convenience shortcut to .showText() === 'plain'
             *
             * @method showPlain
             * @return {Boolean}
             */
            showPlain: function () { return this.showText() === 'plain'; }
        };

        this.loadVariant = function (variant, url, callback) {
            this.variants.load(variant, url, callback);
        };

        this.init = function (variant_data) {
            this.variants.init(variant_data);
        };
    };

    /**
     *  @class SelectionModel
     */
    adhocracy.SelectionModel = function () {

        this.init = function (variantData, selectionDetails) {
            var self = this,
                add = function (name) {
                    if (self.variants.current[name] === undefined) {
                        self.variants.current[name] = ko.observable();
                    }
                };
            this.variants.init(variantData);
            this.selectionDetails = selectionDetails;
            // add possibly missing observables
            add('history');
            add('votes');
            add('delegates');
        };

        this.loadVariant = function (variant, url) {
            var self = this,
            tab = this.currentTab();
            this.variants.load(variant, url, function () {
                // ensure we have the data of the current tab loaded
                self.selectTab(tab, variant);
            });
        };

        this.currentTab = ko.observable('text');
        this.selectTab = function (tab, variant) {
            // load the tabcontend if necessary
            //debugger;
            if ($.inArray(tab, ['history', 'votes', 'delegates']) !== -1) {
                if (variant === undefined) {
                    variant = this.variants.current.variant();
                }
                this.loadTabContents(variant, tab);
            }

            // update currentTab observable if necessary
            if (this.currentTab() !== tab) {
                this.currentTab(tab);
            }
        };

        this.showDiffSwitcher = ko.dependentObservable(function () {
            if (this.variants.current === undefined) {
                // early state where current in not initialized
                return true;
            }
            if (!this.variants.current.is_head() && this.currentTab() === 'text') {
                return true;
            } else {
                return false;
            }
        }.bind(this));

        this.loadTabContents = function (variant, tab) {
            var self = this,
                url,  // the url to load the data from
                cached = this.variants.cache[variant], // the cached variant d.
                current = this.variants.current, // the current variant obj.
                target = current[tab]; // the observable for the content
            console.log([variant, tab, cached]);
            if (cached[tab] !== undefined) {
                // we already have a cached value
                if (target() !== cached[tab]) {
                    // set the target observable to the cached value
                    target(cached[tab]);
                }
            } else {
                // we don't have a cache. Load the tab content
                if (tab === 'history') {
                    url = current.history_url() + '.overlay';
                } else if (tab === 'votes') {
                    url = self.selectionDetails.urls[variant].votes + '.overlay';
                }
                $.ajax({
                    url: url,
                    dataType: 'html',
                    success: function (data) {
                        // save in cache and update the observable
                        cached[tab] = data;
                        target(data);
                    },
                    error: function () {
                        var msg = '<p>error</p>';
                        cached[tab] = msg;
                        target(msg);
                    }
                });
            }
        };

        this.showText = ko.dependentObservable(function () {
            return this.currentTab() === 'text';
        }.bind(this));

        this.showHistory = ko.dependentObservable(function () {
            return this.currentTab() === 'history';
        }.bind(this));

        this.showVotes = ko.dependentObservable(function () {
            return this.currentTab() === 'votes';
        }.bind(this));

        this.showDelegates = ko.dependentObservable(function () {
            return this.currentTab() === 'delegates';
        }.bind(this));
    };
    adhocracy.SelectionModel.prototype = new adhocracy.PaperModel();

}());