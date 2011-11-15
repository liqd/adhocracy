/*jslint vars:true, browser:true, nomen:true */
/*global document:true, jQuery:true, $:true, ko:true */


/**
 * Javascript application code for adhocracy mainly using
 * knockout.js and jquery
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

    var variant_dummy = {"history_url": undefined,
            "is_head": undefined,
            "title": undefined,
            "text_diff": undefined,
            "num_selections": undefined,
            "title_diff": undefined,
            "history_count": undefined,
            "has_changes": undefined,
            "variant": undefined};


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
            current: ko.mapping.fromJS(variant_dummy),
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

        this.init = function (variant_data) {
            this.variants.init(variant_data);
        };
    };

    /**
     *  @class SelectionModel
     */
    adhocracy.SelectionModel = function () {

        this.selectionDetails = {urls: {}};

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

        this.loadTabContents = function (variant, tab) {
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

        this.voteWidget = ko.observable();

        this.doUpdateVoteWidget = function () {
            var variant = this.variants.current.variant(),
                urls = this.selectionDetails.urls[variant],
            voteWidget = this.voteWidget;

            if (this.variants.current !== undefined) {


                if (urls !== undefined) {

                $.ajax({url: urls.poll_widget,
                        success: function (data) {
                            voteWidget(data); },
                        error: function () {
                            voteWidget(''); }});

                }
            } else {
             voteWidget('');
            }

        };

        this.updateVoteWidget = ko.dependentObservable(function () {
            this.doUpdateVoteWidget();
        }.bind(this));

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


$(document).ready(function(){

    var overlayAjaxLoadContent,
        overlayAjaxRebindLinks;

    overlayAjaxLoadContent = function () {

        // grab wrapper element inside content
        var wrap = this.getOverlay().find(".contentWrap");
        var url = this.getTrigger().attr("href") + ".overlay";
        wrap.load(url);
    };

    overlayAjaxRebindLinks = function () {
        // bind links containing the string '.overlay'
        // to a handler that loads the url into the overlay
        var wrap = this.getOverlay().find(".contentWrap");
        $(wrap).delegate('a', 'click', function(event) {
            var href = $(this).attr('href');
            var re = new RegExp('\\.overlay');
            if (re.test(href)) {
                wrap.load(href);
                event.preventDefault();
            }
        });
    };

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

  // initial jquery label_over
  $('.label_over label').labelOver('over-apply');

  // overlay
  $('#overlay-default').overlay({
    // custom top position
    top: '25%'
    // load it immediately after the construction
  });

  //open link in overlay (like help pages)
  $("a[rel=#overlay-ajax]").overlay({
    target: '#overlay-default',
    onBeforeLoad: overlayAjaxLoadContent,
    onLoad: overlayAjaxRebindLinks
  });

  $("a[rel=#overlay-ajax-big]").overlay({
    target: '#overlay-big',
    onBeforeLoad: overlayAjaxLoadContent,
    onLoad: overlayAjaxRebindLinks
  });

});

$('#blog_select_button').click(function () {
  $('#blog_select').toggleClass('open');
  return false;
});
$('body').click(function () {
  $('#blog_select.open').removeClass('open');
});

// comments
$('.comment, .paper').hover(
  function(){
    $(this).find('.hover_active').fadeIn('slow');
  },
  function(){
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
  if(!comment_form) {
      var form_url = '/comment/form/reply/' + reply_id;
      var comment_div = $('#' + c_id);
      // create a container and load the form into it.
      var form_div = comment_div.add('<div></div>').not(comment_div);
      form_div.insertAfter(comment_div);
      form_div.attr('comment_id', c_id);
      form_div.attr('id', comment_form_id);
      form_div.load(form_url, function() {
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
  if(!comment_form) {
      var form_url = '/comment/' + comment_id + '/edit.ajax';
      var comment_div = $('#' + c_id);
      // create a container and load the form into it.
      var form_div = comment_div.add('<div></div>').not(comment_div);
      form_div.insertAfter(comment_div);
      form_div.attr('comment_id', c_id);
      form_div.attr('id', comment_edit_form_id);
      form_div.load(form_url, function() {
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

(function() {
    // function only to get a function local namespace
    var second_level_comments = $('.comments_list > li > ul');
    second_level_comments.hide();
    second_level_comments.toggleClass('open');
})();

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
  if(!comment_form) {
    $('#' + p_id).append('<div id="comment_form_' + p_id + '" comment_id="' + p_id + '">' + comment_form_html + '</div>');
  } else $('#comment_form_' + p_id).remove();
  $(this).toggleClass('open');
  return false;
});

// This is done now by knockout bindings.
// $('.switch_buttons .button_small').click(function () {
//   $('.switch_buttons .button_small').removeClass('active');
//   $(this).addClass('active');
//   return false;
// });

$('.info_box .close_button').click(function() {
  $(this).parent().fadeOut();
});
