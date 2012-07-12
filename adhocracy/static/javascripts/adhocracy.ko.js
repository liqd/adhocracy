/*jslint vars:true, browser:true, nomen:true */
/*global document:true, jQuery:true, $:true, ko:true */


/**
 * Javascript application code for adhocracy mainly using
 * knockout.js and jquery
 *
 * @module adhocracy.ko
 *
 */

var alert = window.alert;

// Make sure we have an "adhocracy" namespace.
var adhocracy = adhocracy || {};

(function () {

    "use strict";

    /***************************************************
     * @namespace: adhocracy.ko
     ***************************************************/

    adhocracy.namespace('adhocracy.ko');

    adhocracy.ko.Badge = function (data) {
        var self = this;
        this.id = ko.observable(data.id);
        this.title = ko.observable(data.title);
        this.description = ko.observable(data.description);
        this.checked = ko.observable(data.checked);
        this.css_class = ko.computed(function () {
            return 'badge badge_' + self.id();
        });
    };

    adhocracy.ko.Badges = function (basepath) {
        var self = this;
        this.id = ko.observable();
        this.title = ko.observable();
        this.badges = ko.observableArray();
        this.clear = function () {
            self.id(undefined);
            self.title(undefined);
            self.badges([]);
        };
        this.load = function (id, callback) {
            self.id(id);
            var url = basepath + id + '/badges.ajax';
            $.get(url, function (data) {
                ko.mapping.fromJS(data, self.mapping, self);
                callback();
            }, 'json').error(
                function (_, textStatus) {
                    alert('Could not get the badges: ' + textStatus);
                }
            );
        };
        this.save = function (callback) {
            var url = basepath + self.id() + '/update_badges.ajax?',
                parameters = $('#edit_badges').serialize();
            $.post(url, parameters, function (data) {
                $('#badges_' + self.id()).html(data.html);
                callback();
            }, 'json').error(function (_, txt) {
                console.log('Error saving the badge: ' + txt);
            });
        };
        this.mapping = {
            badges: {
                create: function (options) {
                    return new adhocracy.ko.Badge(options.data);
                }
            }
        };
    };

    adhocracy.ko.editBadges = function (basepath) {
        var self = this,
            overlay_container;
        this.selected = new adhocracy.ko.Badges(basepath);
        this.cancel = function () {
            self.selected.clear();
            self.overlay_container.overlay().close();
        };
        this.edit = function (data, event) {
            var id = $(event.target).parent().find('.badges').data('id');
            self.selected.load(id, function () {
                self.overlay_container.overlay().load();
            });
        };
        this.save = function () {
            self.selected.save(self.cancel);
        };
        this.applyToPager = function (selector) {
            var containers = $(selector).find('.badges').parent();
            containers.append('<a href="#" class="btn btn-mini edit" ' +
                              'data-bind="click: edit">Edit Badges</a>');
            self.overlay_container = $('#edit_badges_container');
            self.overlay_container.overlay();
            ko.applyBindings(self, $(selector)[0]);
        };
    };

    /**
     * Example for an json object returned for variants.
     * Used to initialze an observable
     */
    adhocracy.ko.variantDummy = {
        "history_url": undefined,
        "is_head": undefined,
        "title": undefined,
        "text_diff": undefined,
        "num_selections": undefined,
        "title_diff": undefined,
        "history_count": undefined,
        "has_changes": undefined,
        "variant": undefined,
        "can_edit": undefined,
        "edit_url": undefined,
        "display_title": undefined,
        "votewidget_url": undefined
    };

    /**
     * @namespace adhocracy
     * @class PaperModel
     */
    adhocracy.ko.PaperModel = function () {

        var viewModel = this;

        /**
         * Observable to store the vote widget for the current variant
         *
         * @method voteWidget
         * @type ko.observable
         */
        this.voteWidget = ko.observable();

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
            switchDiff: ko.observable(false),
            /**
             * The current
             * @property switchDiff
             * @type object (with observeable properties)
             * @default
             */
            current: ko.mapping.fromJS(adhocracy.ko.variantDummy),
            init: function (data) {
                var variant = data.variant;

                this.cache[variant] = data;
                this.current = ko.mapping.fromJS(data, this.current);
                this.current.variant.subscribe(
                    function () { viewModel.updateVoteWidget(); }
                );
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
                            if (callback !== undefined) {
                                callback();
                            }
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

        this.init = function (variantData) {
            this.variants.init(variantData);
        };

        /**
         * Utility function to fetch the current vote widget (without caching
         * it) and store it in the observable this.voteWidget().
         */
        this.updateVoteWidget = function () {
            var variant = this.variants.current.variant(),
                url = this.variants.current.votewidget_url(),
                voteWidget = this.voteWidget,
                clearVoteWidget = function () { voteWidget(''); };

            if (url !== '') {
                $.ajax({
                    url: url,
                    success: function (data) {
                        // update the voteWidget observable
                        voteWidget(data);
                    },
                    error: clearVoteWidget
                });
            } else {
                clearVoteWidget();
            }
        };
    };

    /**
     * A model to work with the selection details overlay.
     *
     * FIXME: delegates tab not implemented.
     *
     * @class adhocracy.SelectionModel
     * @extends adhocracy.PaperModel
     */
    adhocracy.ko.SelectionModel = function () {

        /**
         * Store data related to the selection. Atm this contains
         * only one property: 'urls' with subproperties for each
         * variant.
         *
         * @method selectionDetails
         * @type object
         *
         */
        this.selectionDetails = {urls: {}};

        /**
         * Observable to store the name of the current Tab. This is
         * one of the following strings: 'text', 'history', 'votes'
         * or 'delegates'
         *
         * @method currentTab
         * @type ko.observable
         */
        this.currentTab = ko.observable('text');

        /**
         * Initialize the model
         *
         * @method init
         * @param {json/object} variantData Json/object for the initial
         * variant. Similar to PaperModel.init and variantDummy.
         * @param {json/object} selectionDetails Json/object with details
         * about the selection. See @property selectionDetails
         */
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

        /**
         * Load a variant. See PaperModel.loadVariant()
         * for the signature
         */
        this.loadVariant = function (variant, url) {
            var self = this,
                tab = this.currentTab();
            this.variants.load(variant, url, function () {
                // ensure we have the data of the current tab loaded
                self.selectTab(tab, variant);
            });
        };

        /**
         * Function to call when another tab is loaded. If requied it
         * loads the content with ajax for the tab and current variant, and
         * stores the tab as the @param currentTab.
         *
         * @param {string} tab The name of the tab
         * @param {string} variant The variant if not the current
         * variant (optional)
         */
        this.selectTab = function (tab, variant) {
            // load the tabcontend if necessary
            if ($.inArray(tab, ['history', 'votes', 'delegates']) !== -1) {
                if (variant === undefined) {
                    variant = this.variants.current.variant();
                }
                this.loadTabContents(tab, variant);
            }

            // update currentTab observable if necessary
            if (this.currentTab() !== tab) {
                this.currentTab(tab);
            }
        };

        /**
         * DependendObservable that returns true if the diff switcher
         * should be hidden/inactive. Is notified automatically if other
         * relevant observables change.
         *
         * @method hideDiffSwitcher
         */
        this.hideDiffSwitcher = ko.dependentObservable(function () {
            var currentTab = this.currentTab(),
                current = this.variants.current;
            if (this.variants.current === undefined) {
                // early state where current in not initialized
                return true;
            }
            if (this.currentTab() !== 'text') {
                return true;
            }
            if (this.variants.current.is_head()) {
                return true;
            }
            return false;
        }.bind(this));

        /**
         * Utility function to load a tab content from a cache or with ajax
         * And sets it as the tab content for the current variant.
         * @method loadTabContents
         * @param {string} tab The name of the tab
         * @param {string} variant The variant
         */
        this.loadTabContents = function (tab, variant) {
            var self = this,
                url,  // the url to load the data from
                cached = this.variants.cache[variant], // the cached variant d.
                current = this.variants.current, // the current variant obj.
                target = current[tab]; // the observable for the content
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

        /**
         * Utility function to fetch the current vote widget (without caching
         * it) and store it in the observable this.voteWidget().
         *
         * This is factored out of the ko.dependentObservable to use it
         * during initialization.
         */
        this.doUpdateVoteWidget = function () {
            var variant = this.variants.current.variant(),
                urls = this.selectionDetails.urls[variant],
                voteWidget = this.voteWidget;

            if (urls !== undefined) {
                $.ajax({
                    url: urls.poll_widget,
                    success: function (data) {
                        voteWidget(data);
                    },
                    error: function () {
                        voteWidget('');
                    }
                });

            } else {
                voteWidget('');
            }
        };

        /**
         * dependentObservable to update the vote widget.
         * FIXME: This might be a simple subscriber to
         * this.variants.current.variant
         *
         * @method updateVoteWidget
         * @type ko.dependentObservable
         */
        this.updateVoteWidget = ko.dependentObservable(function () {
            this.doUpdateVoteWidget();
        }.bind(this));

        /**
         * Convenient dependentObservable for less verbose data binding.
         * Indicates to show the text tab.
         *
         * @method showText
         * @type ko.dependentObservable
         */
        this.showText = ko.dependentObservable(function () {
            return this.currentTab() === 'text';
        }.bind(this));

        /**
         * Convenient dependentObservable for less verbose data binding.
         * Indicates to show the history tab.
         *
         * @method showHistory
         * @type ko.dependentObservable
         */
        this.showHistory = ko.dependentObservable(function () {
            return this.currentTab() === 'history';
        }.bind(this));

        /**
         * Convenient dependentObservable for less verbose data binding.
         * Indicates to show the votes tab.
         *
         * @method showVotes
         * @type ko.dependentObservable
         */
        this.showVotes = ko.dependentObservable(function () {
            return this.currentTab() === 'votes';
        }.bind(this));

        /**
         * Convenient dependentObservable for less verbose data binding.
         * Indicates to show the delegates tab.
         *
         * @method showDelegates
         * @type ko.dependentObservable
         */
        this.showDelegates = ko.dependentObservable(function () {
            return this.currentTab() === 'delegates';
        }.bind(this));
    };
    adhocracy.ko.SelectionModel.prototype = new adhocracy.ko.PaperModel();

}());
