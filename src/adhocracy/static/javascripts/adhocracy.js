/*jslint vars:true, browser:true, nomen:true */
/*global document:true, jQuery:true, $:true, ko:true */


/**
 * Javascript application code for adhocracy mainly using
 * knockout.js and jquery
 *
 * @module adhocracy
 *
 */

"use strict";

window.console = window.console || {};
window.console.log = window.console.log || function () {};

// Make sure we have an "adhocracy" namespace.
var adhocracy = adhocracy || {};

(function () {

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

    adhocracy.overlay.rebindCameFrom = function () {
        var came_from = this.getTrigger().attr('href');
        if (came_from === undefined) {
            came_from = window.location.pathname;
        }
        this.getOverlay().find(".patch_camefrom")
            .attr('href', function (i, href) {
                var separator;
                if (href.indexOf('?') !== -1) {
                    separator = '&';
                } else {
                    separator = '?';
                }
                return href + separator + 'came_from=' + came_from;
            });
    };
    adhocracy.overlay.rewriteDescription = function () {
        var description = this.getTrigger().data('description');
        if (description === undefined) {
            description = this.getTrigger().data('title');
        }
        if (description === undefined) {
            description = this.getTrigger().attr('title');
        }
        if (description !== undefined) {
            this.getOverlay().find(".patch_description").html(description);
        }
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
            onBeforeLoad: function (event) {
                adhocracy.overlay.rewriteDescription.call(this, event);
                adhocracy.overlay.rebindCameFrom.call(this, event);
            }
        });

        wrapped.find("a[rel=#overlay-join-button]").overlay({
            fixed: false,
            mask: adhocracy.overlay.mask,
            target: '#overlay-join',
            onBeforeLoad: function (event) {
                adhocracy.overlay.rewriteDescription.call(this, event);
                adhocracy.overlay.rebindCameFrom.call(this, event);
            }
        });

        wrapped.find("a[rel=#overlay-validate-button]").overlay({
            fixed: false,
            mask: adhocracy.overlay.mask,
            target: '#overlay-validate',
            onBeforeLoad: function (event) {
                adhocracy.overlay.rewriteDescription.call(this, event);
                adhocracy.overlay.rebindCameFrom.call(this, event);
            }
        });

    };

    /***************************************************
     * @namespace: adhocracy.tooltips
     ***************************************************/

    adhocracy.namespace('adhocracy.tooltips');

    /**
     * Initialize the tooltips for all correctly marked
     * elements found inside baseSelector. If baseSelector
     * is not given, it searches for all elements in the
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
     * @namespace: adhocracy.helpers
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
    adhocracy.helpers.createSocialButtons = function (selector, tweetText, baseUrl, cookieDomain) {
        var elements = $(selector);
        if (elements.length > 0) {
            elements.socialSharePrivacy({
                services : {
                    facebook: {
                        'dummy_img': baseUrl + '/images/dummy_facebook.png'
                    },
                    twitter : {
                        'dummy_img': baseUrl + '/images/dummy_twitter.png',
                        'tweet_text': tweetText
                    },
                    gplus : {
                        'dummy_img': baseUrl + '/images/dummy_gplus.png'
                    }
                },
                'css_path': '',
                'cookie_domain': cookieDomain
            });
        }
    };

    adhocracy.helpers.initializeTutorial = function (name) {
        $('#start-tutorial-button').click(function (event) {
            $(this).joyride({inline: true,
                             nextButtonText: $(this).data('next'),
                             prevButtonText: $(this).data('previous')});
            event.preventDefault();
        });
        $('#disable-all-tutorials').click(function (event) {
            $.get('/tutorials?disable=ALL');
            $('#tutorial-banner').fadeOut();
            event.preventDefault();
        });
        $('#disable-this-tutorial').click(function (event) {
            $.get('/tutorials?disable=' + name);
            $('#tutorial-banner').fadeOut();
            event.preventDefault();
        });
    };

    adhocracy.helpers.initializeTagsAutocomplete = function (selector) {

        if ($.fn.autocomplete === undefined) {
            return;
        }
        var $selected = $(selector);
        var acUrl = $selected.data('instance-baseurl') + 'tag/autocomplete';
        $selected.autocomplete(acUrl, {
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
                for (i = 0; i < data.length; i += 1) {
                    arr[i] = {data: data[i], value: data[i].display,
                              result: data[i].tag};
                }
                return arr;
            },
            delay: 10
        });
    };

    adhocracy.helpers.initializeUserAutocomplete = function (selector) {

        if ($.fn.autocomplete === undefined) {
            return;
        }

        $(selector).autocomplete('/user/complete', {
            autoFill: false,
            dataType: 'json',
            formatItem: function (data, i, max, val) {
                return data.display;
            },
            formatResult: function (data, i, max, val) {
                return data.user;
            },
            parse: function (data) {
                var arr = [],
                    i;
                for (i = 0; i < data.length; i += 1) {
                    arr[i] = {data: data[i], value: data[i].display,
                        result: data[i].user};
                }
                return arr;
            },
            delay: 10
        });
    };

    adhocracy.helpers.updateBadgePreview = function (selector, color, visible, title) {
        var wrapper = $(selector),
            stylerule,
            styleelement;
        if (title) {
            $('.badge_dummy.abadge').text(title);
        }
        if (color !== undefined) {
            if (!wrapper.is(":visible")) {
                wrapper.removeClass('hidden');
            }
            if (visible) {
                stylerule = '.badge_dummy.abadge:before { color: ' + color + ';}';
            } else {
                stylerule = '.badge_dummy.abadge { visibility: hidden;}';
            }

            if ($('#dummystyle').length === 0) {
                $('head').append(
                    '<style id="dummystyle" type="text/css"></style>'
                );
            }
            $('#dummystyle').text(stylerule);
        }
    };
    adhocracy.helpers.initializeBadgeColorPicker = function (selector, visibleSelector, titleSelector, storagekey) {
        var updatePreview = adhocracy.helpers.updateBadgePreview;
        $(selector).spectrum({
            preferredFormat: "hex",
            showInput: true,
            showPalette: true,
            showSelectionPalette: true,
            localStorageKey: storagekey,
            change: function (color) {
                updatePreview('#badge-preview', color.toHexString(), visibleSelector);
            }
        });
        var update = function() {
            updatePreview('#badge-preview', $(selector).val(), $(visibleSelector).is(':checked'), $(titleSelector).val());
        };
        $(visibleSelector).change(update);
        $(titleSelector).change(update);
        update();
    };

}());

$(document).ready(function () {

    // initial jquery elastic
    $('textarea').elastic();

    adhocracy.tooltips.initialize();
    adhocracy.helpers.initializeFlashMessageDelegates();
    adhocracy.helpers.initializeTagsAutocomplete('#tags');
    adhocracy.helpers.initializeUserAutocomplete(".userCompleted");
    adhocracy.overlay.bindOverlays('body');

    // initial jquery-placeholder
    $('input, textarea').placeholder();

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
        var comment_form = $('#' + comment_form_id).attr('comment_id');
        if (!comment_form) {
            var form_url = $(this).data('reply-url');
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
            var baseUrl = $(this).data('instance-baseurl');
            var form_url = baseUrl + 'comment/' + comment_id + '/edit.ajax';
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

    var stats_baseurl = $('#main_comments').data('stats-baseurl');
    if (stats_baseurl) {
        $('.comment a.show_comments').one('click', function () {
            var c_id = $(this).closest('.comment').attr('id');
            $.get(stats_baseurl + '&cause=showSubcomments&comment_id=' + c_id);
        });
        $(document).one('scroll', function() {
            var c_ids = $('.comment').filter('[id]').map(function() {
                return this.id;
            }).get().sort().join(',');
            $.get(stats_baseurl + '&cause=scroll&comment_id=' + c_ids);
        });
    }

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


    /* Hide hidejs class elements, e.g. input field in user.register */
    $(".hidejs").hide();

    /* Generic buttons that show/hide an element with a specific id.
     * Possible classes and attributes:
     * * 'showhide_button' (class)
     *   The button needs the class showhide_button
     * * 'data-target' (attr)
     *   The button needs an attribute 'data-target' with a selector
     *   string to find the target.
     * * 'data-target-speed' (attr)
     *   Optionally provide a speed for jquery's show()/hide() animations.
     *   Both strings ('slow'/'fast') and milliseconds (e.g. '400') will
     *   work.
     * * 'data-toggle-class', 'data-toggle-element' (attr)
     *   The button can optionally provide a classname in the attribute
     *   data-toggle-class. This class will be assigned to the button if
     *   it is pressed and the target is shown. If not class name is
     *   given, the class 'hidden' will be used. If the button provides an
     *   element selector in the attribute data-toggle-element
     *   the class will be assigned to this
     *   element.
     *   it is pressed and the target is shown. If not class name is
     *   given, the class 'hidden' will be used.
     * * 'data-toggle-text' (attr)
     *   The button can optionally provide a text in the attribute
     *   data-toggle-text. This button will display this text if the target
     *   is button was pressed and the target is visible. If no text
     *   is given, the text of the button won't change.
     * * 'data-cancel' (attr)
     *   The *targed element* needs to have an attribute 'data-cancel'
     *   containing a selector string. The click event of the matching
     *   elements *inside the target* will hide the target an unhide
     *   the button.
     */
    $('body').delegate('.showhide_button', 'click', function (event) {
        event.preventDefault();
        var self = $(this),
            target_selector = self.data('target'),
            target = $(target_selector),
            target_speed = self.data('target-speed'),
            cancel_selector = target.data('cancel'),
            cancel = target.find(cancel_selector),
            toggle_class = self.data('toggle-class') || "hidden",
            toggle_element_selector = self.data('toggle-element'),
            toggle_element,
            toggle_text = self.data('toggle-text'),
            old_text = self.text();

            //debugger;
        if (toggle_element_selector) {
            toggle_element = $(toggle_element_selector);
        } else {
            toggle_element = self;
        }

        if (toggle_element.hasClass(toggle_class)) {
            toggle_element.removeClass(toggle_class);
            target.hide(target_speed);
        } else {
            target.show(target_speed);
            toggle_element.addClass(toggle_class);
        }
        if (toggle_text !== undefined) {
            self.text(toggle_text);
            self.data('toggle-text', old_text);
        }

        // bind a possible cancel action to show the button and hide the target
        cancel.bind('click', function (event) {
            event.preventDefault();
            toggle_element.removeClass(toggle_class);
            target.hide();
        });
    });

    $('body').delegate('select.sort_options', 'change', function (event) {
        event.preventDefault();
        var url = $(this).find('option:selected').data('url');
        window.location.href = url;
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
                target.replaceWith(data);
                adhocracy.overlay.bindOverlays(target);
            }
        });
    });

    $('#feedback_button').toggle(
        function () {
            $('#feedback').animate({right: '0px'});
            return false;
        },
        function () {
            $('#feedback').animate({right: '-350px'});
            return false;
        }
    );

    $('.showmore').each(function () {
        var self = $(this);
        self.find('.showmore_morelink').bind('click', function (event) {
                self.find('.showmore_collapsed').css('display', 'none');
                self.find('.showmore_uncollapsed').css('display', 'inline');
                return false;
            });
        self.find('.showmore_lesslink').bind('click', function (event) {
                self.find('.showmore_collapsed').css('display', 'inline');
                self.find('.showmore_uncollapsed').css('display', 'none');
                return false;
            });
    });

    $('a.expand_arrow').click(function () {
        $(this).parent().toggleClass('expanded');
    });

    $('.facet_check').click(function() {
        $(this).parent().children('a')[0].click();
    });
});
