/*jslint vars:true, browser:true, nomen:true */
/*global document:true, jQuery:true, $:true, ko:true */


/**
 * Javascript application code for adhocracy mainly using
 * knockout.js and jquery
 *
 * @module adhocracy
 *
 */

// Make sure we have an "adhocracy" and namespace.
var adhocracy = adhocracy || {};

(function () {

    "use strict";

    /**
     * General purpose namespace creation and retrivel, taken
     * from Stoyan Stefanov's marvellous book
     * "JavaScript Patterns"
     *
     * @method namespace
     */
    adhocracy.namespace =  function (ns_string) {
        var parts = ns_string.split('.'),
            parent = adhocracy,
            i;
        // strip redundant leading global
        if (parts[0] === "adhocracy") {
            parts = parts.slice(1);
        }
        for (i = 0; i < parts.length; i += 1) {
            // create a property if it doesn't exist
            if (typeof parent[parts[i]] === "undefined") {
                parent[parts[i]] = {};
            }
            parent = parent[parts[i]];
        }
        return parent;
    };


    /***************************************************
     * @namespace: adhocracy.ko
     ***************************************************/

    adhocracy.namespace('adhocracy.ko');

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
        "display_title": undefined
    };

    /**
     * @namespace adhocracy
     * @class PaperModel
     */
    adhocracy.ko.PaperModel = function () {

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
            current: ko.mapping.fromJS(adhocracy.ko.variantDummy),
            init: function (data) {
                var variant = data.variant;
                this.cache[variant] = data;
                this.current = ko.mapping.fromJS(data, this.current);
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

        this.init = function (variantData) {
            this.variants.init(variantData);
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
         * Observable to store the vote widget for the current variant
         *
         * @method voteWidget
         * @type ko.observable
         */
        this.voteWidget = ko.observable();

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

    /***************************************************
     * @namespace: adhocracy.overlay
     ***************************************************/

    adhocracy.namespace('adhocracy.overlay');

    adhocracy.overlay.ajaxLoadContent = function () {
        // grab wrapper element inside content
        var wrap = this.getOverlay().find(".contentWrap");
        var url = this.getTrigger().attr("href") + ".overlay";
        wrap.load(url);
    };

    adhocracy.overlay.ajaxRebindLinks = function () {
        // bind links containing the string '.overlay'
        // to a handler that loads the url into the overlay
        var wrap = this.getOverlay().find(".contentWrap");
        wrap.delegate('a[href*=\\.overlay]', 'click', function (event) {
            var href = $(this).attr('href');
            wrap.load(href);
            event.preventDefault();
        });
    };

    adhocracy.overlay.rebindCameFrom = function() {
        var came_from = this.getTrigger().attr('href');
        if (came_from==null) {came_from=window.location.pathname};
        this.getOverlay().find(".patch_camefrom").attr('href', function(i, href) {
            return href.split('?')[0]+'?came_from='+came_from;
        });
    };
    adhocracy.overlay.rewriteDescription = function() {
        var description = this.getTrigger().data('description');
        if (description==null) {description = this.getTrigger().data('title')};
        if (description!=null) {
            this.getOverlay().find(".patch_description").html(description);
        };
    };

    adhocracy.overlay.mask = {
        color: '#111',
        opacity: 0.9,
        loadSpeed: 'fast'
    };

    adhocracy.overlay.bindOverlays = function (element) {
        var wrapped = $(element);
        wrapped.find('#overlay-default').overlay({
            // custom top position
            fixed: false,
            top: '25%'
        });

        //open link in overlay (like help pages)
        wrapped.find("a[rel=#overlay-ajax]").overlay({
            fixed: false,
            target: '#overlay-default',
            mask: adhocracy.overlay.mask,
            onBeforeLoad: adhocracy.overlay.ajaxLoadContent,
            onLoad: adhocracy.overlay.ajaxRebindLinks
        });

        wrapped.find("a[rel=#overlay-ajax-big]").overlay({
            fixed: false,
            mask: adhocracy.overlay.mask,
            target: '#overlay-big',
            onBeforeLoad: adhocracy.overlay.ajaxLoadContent,
            onLoad: adhocracy.overlay.ajaxRebindLinks
        });

        wrapped.find("a[rel=#overlay-login-button]").overlay({
            fixed: false,
            mask: adhocracy.overlay.mask,
            target: '#overlay-login',
            onBeforeLoad: function(event) {
                adhocracy.overlay.rewriteDescription.call(this, event);
                adhocracy.overlay.rebindCameFrom.call(this, event);
            }
        });

        wrapped.find("a[rel=#overlay-join-button]").overlay({
            fixed: false,
            mask: adhocracy.overlay.mask,
            target: '#overlay-join',
            onBeforeLoad: adhocracy.overlay.rewriteDescription,
        });

    };

    /***************************************************
     * @namespace: adhocracy.tooltip
     ***************************************************/

    adhocracy.namespace('adhocracy.tooltips');

    /**
     * Initialize the tooltips for all correctly marked
     * elements found inside baseSelector. If baseSelector
     * is not given, it searchs for all elements in the
     * document body.
     *
     * @param {string} baseSelector A selector string that can be
     * passed to jQuery. Optional, defaults to 'body'.
     */
    adhocracy.tooltips.initialize = function (baseSelector) {
        baseSelector = baseSelector || 'body';
        $(baseSelector).find(".ttip[title]").tooltip({
            position: "bottom left",
            opacity: 1,
            effect: 'toggle'
        }).dynamic({ bottom: { direction: 'down', bounce: true } });
    };


    /***************************************************
     * @namespace: adhocracy.tooltip
     ***************************************************/

    adhocracy.namespace('adhocracy.helpers');

    /**
     * Initialize delegates that implement the close function for
     * flash messages and info boxes
     */
    adhocracy.helpers.initializeFlashMessageDelegates = function () {

        var fadeParent;

        fadeParent = function (event) {
            event.preventDefault();
            $(this).parent().fadeOut();
        };
        $('body').delegate('.info_box .close_button', 'click', fadeParent);
        $('body').delegate('.alert-message .close_button', 'click', fadeParent);
    };

    /*
     * Initialize twitter, facebook and google+ buttons in the element(s)
     * selector.
     *
     * @param {string, dom element or jquery element} selector Something
     * to wrap into the jQuery function to find the container element(s)
     * @param {string} text The text for the tweet. It will be chopped
     * to 120 Characters.
     * @param {string} baseUrl The url from where the plugins 'image'
     * folder is served. if not given it will be relative to the current
     * page.
     */
    adhocracy.helpers.createSocialButtons = function (selector, tweetText, baseUrl) {
        var elements = $(selector);
        if (elements.length > 0) {
            elements.socialSharePrivacy({
                services : {
                    facebook: {
                        'dummy_img': baseUrl + '/images/dummy_facebook.png',
                        'perma_option': 'off'
                    },
                    twitter : {
                        'dummy_img': baseUrl + '/images/dummy_twitter.png',
                        'perma_option': 'off',
                        'tweet_text': tweetText
                    },
                    gplus : {
                        'dummy_img': baseUrl + '/images/dummy_gplus.png',
                        'perma_option': 'off'
                    }
                },
                'css_path': ''
            });
        }
    };

    adhocracy.helpers.initializeTutorial = function () {
        $('#start-tutorial').click(function (event) {
            $(this).joyride({inline: true});
            event.preventDefault();
        });
        $('#disable-tutorials').click(function (event) {
            $.get('/tutorials?disable=1');
            $('#tutorial-banner').fadeOut();
            event.preventDefault();
                });
    };

    adhocracy.helpers.initializeTagsAutocomplete = function (selector) {

        $("#tags").autocomplete('/tag/autocomplete', {
            autoFill: false,
            dataType: 'json',
            formatItem: function (data, i, max, val) {
                return data.display;
            },
            formatResult: function (data, i, max, val) {
                return data.tag;
            },
            parse: function (data) {
                var arr = [],
                    i;
                for (i = 0; i < data.length; i++) {
                    arr[i] = {data: data[i], value: data[i].display,
                    result: data[i].tag};
                }
                return arr;
            },
            delay: 10
        });
    };

}());

$(document).ready(function () {

    'use strict';

  // initial jquery slide
    $("#slides").slides({
        generatePagination: false,
        effect: 'fade'
    });

    // initial jquery elements circle
    $("#projects_slides").multipleElementsCycle({
        start: 0
    });

    // initial jquery elastic
    $('textarea').elastic();

    adhocracy.tooltips.initialize();
    adhocracy.helpers.initializeFlashMessageDelegates();
    adhocracy.helpers.initializeTagsAutocomplete('#tags');
    adhocracy.overlay.bindOverlays('body');

    // initial jquery label_over
    $('.label_over label').labelOver('over-apply');


    $('#blog_select_button').click(function () {
        $('#blog_select').toggleClass('open');
        return false;
    });
    $('body').click(function () {
        $('#blog_select.open').removeClass('open');
    });

    // comments
    $('.comment, .paper').hover(
        function () {
            $(this).find('.hover_active').fadeIn('slow');
        },
        function () {
            $(this).find('.hover_active').fadeOut('fast');
        }
    );

    $('.comment a.show_comments').click(function () {
        var c_id = $(this).closest('.comment').attr('id');
        $('#' + c_id + '_comments').toggle();
        $(this).toggleClass('open');
        return false;
    });

    // get a comment reply form and insert it into the page

    $('.comment a.new_comment').click(function (event) {
        event.preventDefault();
        var c_id = $(this).closest('.comment').attr('id');
        var comment_form_id = 'comment_form_' + c_id;
        var reply_id = $(this).data('reply');
        var comment_form = $('#' + comment_form_id).attr('comment_id');
        if (!comment_form) {
            var form_url = '/comment/form/reply/' + reply_id;
            var comment_div = $('#' + c_id);
            // create a container and load the form into it.
            var form_div = comment_div.add('<div></div>').not(comment_div);
            form_div.insertAfter(comment_div);
            form_div.attr('comment_id', c_id);
            form_div.attr('id', comment_form_id);
            form_div.load(form_url, function () {
                form_div.find('a.cancel').click(function (event) {
                    // the cancel button removes the form from the dom
                    form_div.remove();
                    event.preventDefault();
                });
            });
        } else {
            $('#comment_form_' + c_id).remove();
        }
        $(this).toggleClass('open');
    });

    // load the comment edit form into the page

    $('.comment a.edit_comment').click(function (event) {
        event.preventDefault();
        var c_id = $(this).closest('.comment').attr('id');
        var comment_edit_form_id = 'comment_edit_form_' + c_id;
        var comment_id = $(this).data('comment');
        var comment_form = $('#' + comment_edit_form_id).attr('comment_id');
        if (!comment_form) {
            var form_url = '/comment/' + comment_id + '/edit.ajax';
            var comment_div = $('#' + c_id);
            // create a container and load the form into it.
            var form_div = comment_div.add('<div></div>').not(comment_div);
            form_div.insertAfter(comment_div);
            form_div.attr('comment_id', c_id);
            form_div.attr('id', comment_edit_form_id);
            form_div.load(form_url, function () {
                // when loaded:
                comment_div.hide();
                form_div.find('a.cancel').click(function (event) {
                    // the cancel button removes the form from the dom
                    form_div.remove();
                    comment_div.show();
                    event.preventDefault();
                });
            });
        } else {
            $('#' + comment_edit_form_id).remove();
        }
    });

    $('.comment_status .button_small').live('click', function (event) {
        event.preventDefault();
        var comment_form = $(this).closest('form');
        comment_form.find('.comment_status .button_small').removeClass('active');
        $(this).addClass('active');
        var new_sentiment = $(this).data('status');
        comment_form.find('input[name="sentiment"]').attr('value', new_sentiment);
    });

    (function () {
        // function only to get a function local namespace
        var second_level_comments = $('.comments_list > li > ul');
        second_level_comments.hide();
        second_level_comments.toggleClass('open');
    }());

    $('.paper a.show_comments').click(function () {
        var p_id = $(this).closest('.paper').attr('id');
        $('#' + p_id + '_comments').toggle();
        $(this).toggleClass('open');
        return false;
    });

    $('.paper a.new_comment').click(function () {
        var comment_form_html = $('#comment_form_template').html();
        var p_id = $(this).closest('.paper').attr('id');
        var comment_form = $('#comment_form_' + p_id).attr('comment_id');
        if (!comment_form) {
            $('#' + p_id).append('<div id="comment_form_' + p_id +
                                 '" comment_id="' + p_id + '">' +
                                 comment_form_html + '</div>');
        } else {
            $('#comment_form_' + p_id).remove();
        }

        $(this).toggleClass('open');
        return false;
    });

    $('.follow_paper').hover(
        function () {
            var button = $(this),
                text = button.data('hover-text');
            button.text(text);
        },
        function () {
            var button = $(this),
                text = button.data('text');
            button.text(text);
        }
    );


    /* Armed labels: Use label text as pre-filling text for empty form fields. */
    $(".armlabel").each(function (e) {
        var hint = $("[for=" + $(this).attr("name") + "]").text();
        var field = this;

        $(this).focus(function () {
            if ($(field).hasClass("armed")) {
                $(field).val("");
                $(field).removeClass("armed");
            }
        });

        $(this).blur(function () {
            if ($.trim($(field).val()).length === 0) {
                $(field).val(hint);
                $(field).addClass("armed");
            }
        });
        $(this).blur();
    });

    /* Make sure that we do not submit placeholder texts */
    $("form").submit(function () {
        $(".armed").each(function (i) {
            $(this).val("");
        });
    });

    /* Hide hidejs class elements, e.g. input field in user.register */
    $(".hidejs").hide();

    /* Generic buttons that show/hide an element with a specific id.
     * Requriements:
     * * The button needs the class showhide_button
     * * and an attribute 'data-target' with a selector string to find
     *   the target.
     * * The targed element needs to have an attribute 'data-cancel'
     *   containing a selector string. The click event of the matching
     *   elements *inside the target* will hide the target an unhide
     *   the button.
     */
    $('body').delegate('.showhide_button', 'click', function (event) {
        event.preventDefault();
        var self = $(this),
            target_selector = self.data('target'),
            target = $(target_selector),
            cancel_selector = target.data('cancel'),
            cancel = target.find(cancel_selector);

        target.show();
        self.hide();

        // bind a possible cancel action to show the button and hide the target
        cancel.bind('click', function (event) {
            event.preventDefault();
            self.show();
            target.hide();
        });
    });

    $('body').delegate('a.do_vote', 'click', function (event) {
        event.preventDefault();
        var self = $(this),
            target = self.closest('.vote_wrapper'),
            splitted,
            widget_url;
        splitted = self.attr('href').split('?');
        widget_url = splitted[0] + '.overlay?' + splitted[1];
        $.ajax({
            url: widget_url,
            success: function (data) {
                target.html(data);
                adhocracy.overlay.bindOverlays(target);
            }
        });
    });
});
