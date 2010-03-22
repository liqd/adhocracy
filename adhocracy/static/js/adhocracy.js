$(document).ready(function() {
	
	jQuery(document).ready(function() {
		  jQuery('abbr.timeago').timeago();
	});
	
	$('.ttip[title]').qtip({ 
	    style: {
            background: '#fdfbc0',
            textAlign: 'left',
            border: {
                width: 2,
            },
            tip: 'topMiddle',
            name: 'cream'
        },
        position: {
            corner: {
                target: 'bottomMiddle',
                tooltip: 'topMiddle'
            }
        },
        show: {
            delay: 70
        }});
    
	$('.otip[title]').qtip({ 
	    style: {
            background: '#fdfbc0',
            textAlign: 'left',
            border: {
                width: 2,
            },
            tip: 'bottomMiddle',
            name: 'cream'
        },
        position: {
            corner: {
                target: 'topMiddle',
                tooltip: 'bottomMiddle'
            }
        },
        show: {
            delay: 70
        }});
        
    $(".hidejs").hide();
    $(".showjs").show();
	
	adhocracyDomain = function() {
		return document.domain.substring(document.domain.split('.')[0].length);
	}
	
	submitForm = function(id) {
		$("#" + id).submit();
	}
	
	moreTags = function() {
	    $(".moreTags").show();
	    $(".moreTagsLink").hide();
	}
	
	/* Tag area add form */
	addTags = function(id) {
	    $(".addtags").slideToggle('fast');
	    return false;
	}
		
	/* Auto-appends */ 
	appendAlternative = function() {
		newElem = $(".alternative.prototype").clone();
		newElem.removeClass('prototype');
		newElem.slideDown('fast');
		newElem = newElem.insertAfter($(".alternative:last"));
		return false;
	}	
	
	appendCanonical = function() {
		newElem = $(".canonical.prototype").clone();
		newElem = newElem.insertAfter($(".canonical:last"));
		newElem.slideDown('fast');
		newElem.removeClass('prototype');
		return false;
	}
	
	$(".userCompleted").autocomplete('/user/complete', {
		autoFill: false,
		dataType: 'json',
		formatItem: function(data, i, max, val) {
			return data.display;
		}, 
		formatResult: function(data, i, max, val) {
			return data.user;
		},
		parse: function(data) {
			var arr = new Array();
			for(var i=0;i<data.length;i++) {
				arr[i] = {data:data[i], value:data[i].display, result:data[i].user};
			}
			return arr;
		},
		delay: 10,
	});
	
	$("#tags").autocomplete('/tag/autocomplete', {
		autoFill: false,
		dataType: 'json',
		formatItem: function(data, i, max, val) {
			return data.display;
		}, 
		formatResult: function(data, i, max, val) {
			return data.tag;
		},
		parse: function(data) {
			var arr = new Array();
			for(var i=0;i<data.length;i++) {
				arr[i] = {data:data[i], value:data[i].display, result:data[i].tag};
			}
			return arr;
		},
		delay: 10,
	});
	
	comment_reply = function(id) {
		$("#tile_c" + id + " .reply_form").slideToggle('fast');
		return false;
	}
	
	comment_link_discussion = function(id) {
		$("#c" + id + " .link_discussion").slideToggle('fast');
		return false;
	}
	
	comment_edit = function(id) {
		$("#tile_c" + id + " .hide_edit").slideToggle('fast');
		$("#tile_c" + id + " .edit_form").slideToggle('fast');
		return false;
	}
	
	comment_hide = function(id) {
		$("#tile_c" + id + " .hide").hide();
		$("#tile_c" + id + " .meta").hide();
		$("#tile_c" + id + " .text").hide();
		$("#tile_c" + id + " .edit_form").hide();
		$("#tile_c" + id + " .reply_form").hide();
		$("#c" + id + " .sub").hide();
		$("#tile_c" + id + " .show").show();
		return false;
	}
	
	comment_show = function(id) {
		$("#tile_c" + id + " .show").hide();
		$("#tile_c" + id + " .meta").show();
		$("#tile_c" + id + " .text").show();
		$("#c" + id + " .sub").show();
		$("#tile_c" + id + " .hide").show();
		$("#c" + id + " .edit_form").hide();
		$("#c" + id + " .reply_form").hide();
		return false;
	}
	
	rate = function(elem_id, poll_id, value) {
	    $(elem_id + " .score").text('*');
		$.post('/poll/' + poll_id + '/vote.json', {position: value},
			function(data) {
				$(elem_id + ".upvoted").removeClass("upvoted");
				$(elem_id + ".downvoted").removeClass("downvoted");
				if (data.decision && data.decision.decided) {
				    if (data.decision.result == -1) {
    					$(elem_id).addClass("downvoted");
    				} 
    				if (data.decision.result == 1) {
    					$(elem_id).addClass("upvoted");
    				}
				}
				$(elem_id + " .score").text(data.score);
			}, 'json');
		return false;
	}
    
	
	add_canonical = function() {
		$(".add_canonical").slideToggle('normal');
		return false;
	}

	$(".comment .hide").show();
	
	/* Mark up the comment selected via a URL anchor (i.e. after editing and creation) */
	anchor = document.location.hash;
	if (anchor.length > 1) {
		$("#tile_" + anchor.substring(1)).addClass("anchor");
		$("#tile_" + anchor.substring(1)).parents().show();
		setTimeout(function() {
			$("#tile_" + anchor.substring(1)).removeClass("anchor");
			}, 3500);
	}
		
	/* Hovering title warnings */
	current_htWarn_title = "";
	$(".htwarn").hover(
			function() {
				current_htWarn_title = $(this).attr('title');
				$(this).append($("<div class='htwarnbox'>" + current_htWarn_title + "</div>"));
				$(this).attr('title', '');
			},
			function() {
				$(this).find(".htwarnbox").remove();
				$(this).attr('title', current_htWarn_title);
			});
	
	/* Live filter for issue listing on instance home page */
	var originalListing = null;
	
	live_filter = function(id, url) { 
		$("#" + id + "_q").keyup(function(fld) {
			if (!originalListing) {
				originalListing = $("#" + id + "_table").html();
			}
			var destination = $("#" + id + "_table");
			var value = $.trim($(this).val());
			if (value.length == 0) {
				destination.html(originalListing);
			}
			$.get(url + '?' + id + '_q=' + value, function(data, status) {
				destination.html(data);
			}, 'text');
		});
	}
	
	live_filter('users', '/user/filter');
	live_filter('serp', '/search/filter');
	live_filter('issues', '/issue/filter');
	live_filter('proposals', '/proposal/filter');
	
	
	/* Armed labels: Use label text as pre-filling text for empty form fields. */
	$(".armlabel").each(function(e) {
		var hint = $("[for=" + $(this).attr("name") + "]").text();
		var field = this; 
		
		$(this).focus(function(){
			if ($(field).hasClass("armed")) {
				$(field).val("");
				$(field).removeClass("armed");
			}
		});
		
		$(this).blur(function() {
			if ($.trim($(field).val()).length==0) {
				$(field).val(hint);
				$(field).addClass("armed");
			}
		});
		$(this).blur();
	});
	
	/* Make sure that we do not submit placeholder texts */
	$("form").submit(function() {
		$(".armed").each(function(i) {
			$(this).val("");
		});
	});
	
	/* Show other proposals regarding an issue when hovering the issue title on the proposal page */
	$("#top_issue").hover(function() {
		$("#issue_details").slideDown(60);
	}, function() {
		$("#issue_details").slideUp(60);
	});
	
	
	/* Sparklines */
	$(".sparkline").each(function(e) {
	    var url = $(this).attr('title');
	    var sparkline = this; 
	    $.getJSON(url, function(data) {
	        $(sparkline).sparkline(data.activity, 
	                        {type: 'bar', 
	                         barWidth: 5, 
	                         barColor: '#999',
	                         height: '10px'});
	        $(sparkline).addClass('loaded');
	    });
	});
});