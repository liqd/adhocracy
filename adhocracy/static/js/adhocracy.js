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
			alert("fR" + data.user + "val" + val);
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
				if (value == -1) {
					$("#tile_c" + id + ".upvoted").removeClass("upvoted");
					$("#tile_c" + id + "").addClass("downvoted");
				} else {
					$("#tile_c" + id + ".downvoted").removeClass("downvoted");
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
		
	anchor = document.location.hash;
	if (anchor.length > 1) {
		$("#tile_" + anchor.substring(1)).addClass("anchor");
		setTimeout(function() {
			$("#tile_" + anchor.substring(1)).removeClass("anchor");
			}, 3500);
	}
	
	hide_tutu = function() {
		if (!$.cookie('hide_tutu')) {
			$(".tutu").slideUp('slow');
		} else {
			$(".tutu").hide();
		}
		$.cookie('hide_tutu', 'yes', {expire: 1000, domain: adhocracyDomain()})
	}
	
	check_tutu = function() {
		if($.cookie('hide_tutu')) {
			hide_tutu();
		} else {
			$('.tutu').slideDown('fast');
		}
	}
	
	check_tutu();
	
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
	
	/* Live filter */ 
	
	var originalListing = null;
	$("#issues_q").keyup(function(fld) {
		
		if (!originalListing) {
			originalListing = $("#issues_table").html();
		}
		var value = $(this).val();
		if ($.trim(value).length==0) {
			$("#issues_table").html(originalListing);
		}
		
		$.get('/instance/test/filter', {'issues_q': value}, function(data, status) {
			$("#issues_table").html(data);
		}, 'text');
	});
	
	/* Armed labels */
	_get = function(e) {
		if (e.type=="textarea") {
			return $(e).text();
		} else {
			return $(e).val();
		}
	}
	
	_set = function(e, s) {
		if (e.type=="textarea") {
			$(e).text(s);
		} else {
			$(e).val(s);
		}
	}
	
	_unset = function(e) {
		_set(e, "");
	}
	
	arm = function(e, hint) {
						
		$(e).focus(function(){
			if ($(e).hasClass("armed")) {
				_unset(e);
				$(e).removeClass("armed");
			}
		});
		
		on_blur = function() {
			if ($(e).hasClass("armed")) {
				return;
			}
			
			if ($.trim($(e).val()).length==0) {
				_set(e, hint);
				$(e).addClass("armed");
			}
		}
		
		$(e).blur(on_blur);
		on_blur();
	}
	
	$(".armlabel").each(function(e) {
		hint = $("[for=" + $(this).attr("name") + "]").text();
		arm(this, hint);
	});
	
	$("form").submit(function() {
		$("[name=" + this.name + "] .armed").each(function(i) {
			_unset(this);
		});
	});
	
	$("#top_issue").hover(function() {
		$("#issue_details").slideDown(60);
	}, function() {
		$("#issue_details").slideUp(60);
	});
	
});