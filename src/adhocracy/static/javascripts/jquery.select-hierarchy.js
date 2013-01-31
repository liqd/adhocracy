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
            placeholder: '------'
        };
        var options = $.extend(defaults, options);
        var obj = $(this);
        var max_depth = 1;

        var choices = obj.find('option').map(function(){
            var val = $(this).val();

            if (val) {
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

        if (options.hideOriginal) {
            obj.hide();
        }
        obj.attr('disabled', 'disabled');
        obj.wrap('<span class="drilldown-wrapper" />');
        obj.after('<select class="drilldown-1"><option value="">' + options.placeholder + '</option></select>');
        var root_select = obj.next();
                       
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
                this_select.after('<select><option value="">' + options.placeholder +'</option></select>');
		
                var next_select = this_select.next();
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

                new_header = $('<div>').addClass('select_header').text(node['header']);

                this_select.after(new_header);
	        }
        }
        root_select.change(change_handler);
    };
})(jQuery);
