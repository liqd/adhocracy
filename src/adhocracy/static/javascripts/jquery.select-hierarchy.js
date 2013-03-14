/**
 * jquery-select-hierarchy
 *
 * Turns a single select containing breadcrumb trails into multiple dynamic selects to allow easy drill-down
 *
 * Author: Andrew Ingram (andy@andrewingram.net)
 */
(function($){
    $.fn.selectHierarchy = function(options) {        
        var defaults = {
            separator: ' > ',
            hideOriginal: true,
            placeholder: '------',
            include_empty_options: true,
            add_empty_default: false
        };
        var options = $.extend(defaults, options);
        var obj = $(this);
        var max_depth = 1;

        var choices = obj.find('option').map(function(){
            var val = $(this).val();

            if (options.include_empty_options || val) {
                var txt = $(this).text();
                var segments = txt.split(options.separator);
                var depth = segments.length;

                if (depth > max_depth) {
                    max_depth = depth;
                }

                var result = {
                    label: txt,
                    short_label: segments[depth-1],
                    value: val,
                    depth: depth,
                    children: [],
                    header: $(this).data('header')
                };

                return result;
            }   
        });

        var roots = [];

        // Build up child values
        for (var depth=1; depth<=max_depth; depth++) {
            $.each(choices, function() {
                var parent = this;

                if (parent.depth==depth) {
                    if (depth===1) {
                        roots.push(this);
                    }

                    $.each(choices, function() {
                        var child = this;
                        if (child.depth == depth+1 && child.label.match("^"+parent.label)==parent.label) { 
                            parent.children.push(child);
                        }
                    });
                }
            });
        }

        var initial_text = obj.children('option:selected').text();

        if (options.hideOriginal) {
            obj.hide();
        }
        obj.wrap('<span class="drilldown-wrapper" />');
        var root_select = $('<select>').addClass('drilldown-1');
        obj.after(root_select);
        if (options.add_empty_default) {
            root_select.add('<option value="">' + options.placeholder + '</option>');
        }
                       
        root_select.data('depth', 1);
                            
        $.each(roots, function(){
            var opt = $('<option>');
            opt.val(this.value);
            opt.text(this.short_label);
            opt.data('node', this);
            root_select.append(opt);
        });
                                
        var change_handler = function(){
            var this_select = $(this);
            var opt = this_select.find('option:selected');
            var node = opt.data('node');
       
            if (this_select.val()) {
                obj.val(this_select.val());
            } else if (this_select.data('depth') > 1) {
                obj.val(this_select.prev().val());
            } else {
                obj.val('');
            }

            this_select.nextAll('select').remove();
            this_select.nextAll('.select_header').remove();

            // Check to see if there's any children, if there are we build another select box;
            if (node && node.children.length > 0) {
                var next_select = $('<select>');
                this_select.after(next_select);
                if (options.add_empty_default) {
                    root_select.add('<option value="">' + options.placeholder + '</option>');
                }

                next_select.addClass('drilldown-' + (node.depth + 1));
                next_select.data('depth', node.depth + 1);
		
                $.each(node.children, function(){
                    var opt = $('<option>');
                    opt.val(this.value);
                    opt.text(this.short_label);
                    opt.data('node', this);
                    next_select.append(opt);
                });
                next_select.change(change_handler);
                next_select.children(':first').attr('selected', 'selected');
                next_select.trigger('change');

                new_header = $('<div>').addClass('select_header').text(node['header']);

                this_select.after(new_header);
	        }
        }
        root_select.change(change_handler);

        var preselect = function (initial_text, level) { 
            var sel = $('.drilldown-'+level);
            
            sel.children('option').each(function () {
                var text = $(this).text();

                if (text === initial_text) {
                    $(this).attr('selected', 'selected');
                } else {
                    var text1 = text + options.separator;
                    if (initial_text.substr(0, text1.length) == text1) {
                        $(this).attr('selected', 'selected');
                        sel.trigger('change');
                        preselect(initial_text.substr(text1.length, initial_text.length), level+1);
                    }
                }
            });

        };

        if (initial_text) {
            preselect(initial_text, 1);
        } else {
            root_select.children(':first').attr('selected', 'selected');
            root_select.trigger('change');
        }
    };
})(jQuery);
