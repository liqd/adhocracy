$(document).ready(function(){
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

    onBeforeLoad: function() {
      // grab wrapper element inside content
      var wrap = this.getOverlay().find(".contentWrap");
      var url = this.getTrigger().attr("href") + ".overlay";
      wrap.load(url);
      //   var rebind = function(links) {
      //       links.click(function(event) {
      //           wrap.load(this.attr("href"));
      //       });
      //   };
      // var links = wrap.find('a');


      //   });
      //   }
    }
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

$('.comment a.new_comment').click(function () {
  var comment_form_html = $('#comment_form_template').html();
  var c_id = $(this).closest('.comment').attr('id');
  var comment_form = $('#comment_form_' + c_id).attr('comment_id');
  if(!comment_form) {
    $('#' + c_id).append('<div id="comment_form_' + c_id + '" comment_id="' + c_id + '">' + comment_form_html + '</div>');
  } else $('#comment_form_' + c_id).remove();
  $(this).toggleClass('open');
  return false;
});

$('.comment_status .button_small').live('click', function () {
  $('.comment_status .button_small').removeClass('active');
  $(this).addClass('active');
  return false;
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
