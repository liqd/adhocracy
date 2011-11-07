/*jslint vars:true, browser:true, nomen:true */
/*global document:true, jQuery:true, $:true */

var viewModel = {
    variants: {}, // cache variants
    switch_diff: ko.observable(true), // state of the changes_switch selector
    current: ko.mapping.fromJS(init_variant), // the current paper
    // show a certain *variant*. Load the data with
    // ajax from the *href* if it is not in the cache
    load: function (variant, href) {
        var exists = false,
            model = this,
            update_model;

        update_model = function () {
            ko.mapping.fromJS(model.variants[variant], model.current);
        };

        if (this.variants[variant] !== undefined) {
            update_model();
        } else {
            $.getJSON(href, {variant_json: '1'},
                      function(data) {
                          model.variants[data.variant] = data;
                          update_model();
                      });
        }
    },
    // Decide how the paper will be displayed.
    // Returns 'plain' or 'diff' depending on the state of the
    // diff switcher and the selected variant.
    show: function () {
        if (this.current.is_head()) {
            return 'plain';
        }
        if (this.switch_diff()) {
            return 'diff';
        }
        return 'plain';
    },
    // convenience functions
    show_diff: function () { return this.show() === 'diff'; },
    show_plain: function () { return this.show() === 'plain'; }
};

// init the model
viewModel.variants[init_variant.variant] = init_variant;
viewModel.load(init_variant.variant);
ko.applyBindings(viewModel);
