$(document).ready(function() {
	
	jQuery(document).ready(function() {
		  jQuery('abbr.timeago').timeago();
	});
	
	
	adhocracyDomain = function() {
		return document.domain.substring(document.domain.split('.')[0].length);
	}
	
	submitForm = function(id) {
		$("#" + id).submit();
	}
		
	/* Auto-appends */ 
	appendRelation = function() {
		newElem = $(".relation.prototype").clone();
		newElem.removeClass('prototype');
		newElem.slideDown('fast');
		newElem = newElem.insertAfter($(".relation:last"));
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
	
	comment_karma = function(id, value) {
		$.getJSON('/karma/give.json', {comment: id, value: value},
			function(data) {
				$("#tile_c" + id + ".upvoted").removeClass("upvoted");
				$("#tile_c" + id + ".downvoted").removeClass("downvoted");
				if (data.position == -1) {
					$("#tile_c" + id + "").addClass("downvoted");
				} 
				if (data.position == 1) {
					$("#tile_c" + id + "").addClass("upvoted");
				}
				$("#tile_c" + id + " .score").text(data.score);
			});
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
	$("#issues_q").keyup(function(fld) {
		
		if (!originalListing) {
			originalListing = $("#issues_table").html();
		}
		var value = $(this).val();
		if ($.trim(value).length==0) {
			$("#issues_table").html(originalListing);
		}
		var instance_key = $("#instance_key").val();
		$.get('/instance/' + instance_key + '/filter', {'issues_q': value}, function(data, status) {
			$("#issues_table").html(data);
		}, 'text');
	});
	
	$("#users_q").keyup(function(fld) {
		
		if (!originalListing) {
			originalListing = $("#users_table").html();
		}
		var value = $(this).val();
		if ($.trim(value).length==0) {
			$("#users_table").html(originalListing);
		}
		$.get('/user/filter', {'users_q': value}, function(data, status) {
			$("#users_table").html(data);
		}, 'text');
	});
	
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
		
		on_blur = function() {
			if ($.trim($(field).val()).length==0) {
				$(field).val(hint);
				$(field).addClass("armed");
			}
		}
		
		$(this).blur(on_blur);
		on_blur();
	});
	
	/* Make sure that we do not submit placeholder texts */
	$("form").submit(function() {
		$("[name=" + this.name + "] .armed").each(function(i) {
			$(i).val("");
		});
	});
	
	/* Show other proposals regarding an issue when hovering the issue title on the proposal page */
	$("#top_issue").hover(function() {
		$("#issue_details").slideDown(60);
	}, function() {
		$("#issue_details").slideUp(60);
	});
	
});