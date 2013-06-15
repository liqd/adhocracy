"use strict";
/*
    Simple OpenID Plugin
    http://code.google.com/p/openid-selector/
    With modifications from the adhocracy project.
    
    This code is licensed under the New BSD License.
*/


var openid;
(function ($) {

/* Configuration starts here */
var providers_large = {
    google : {
        name : 'Google',
        url : 'https://www.google.com/accounts/o8/id'
    },
    yahoo : {
        name : 'Yahoo',
        url : 'https://me.yahoo.com'
    },
    openid : {
        name : 'OpenID',
        label : 'Enter your OpenID.',
        url : null
    }
};
var providers_small = {};

/* Configuration ends here */



var providers;
openid = {
    version : '1.3-adhocracy', // version constant
    demo : false,
    cookie_expires : 6 * 30, // 6 months.
    cookie_name : 'openid_provider',
    cookie_path : '/',

    img_path : '/openid-selector/images/',

    all_small : false, // output large providers w/ small icons
    no_sprite : false, // don't use sprite image
    image_title : '{provider}', // for image title

    init : function() {
        providers = $.extend({}, providers_large, providers_small);
        var self = this;

        $('.openid_form').each(function(i, form) {
            var $form = $(form);
            if ($form.attr('data-openid-initialized')) {
                return;
            }
            $form.attr('data-openid-initialized', 'true');

            var $openid_btns = $form.find('.openid_btns');
            var i = 0;
            // add box for each provider
            for (var id in providers_large) {
                var box = self.getBox($form, id, providers_large[id], (self.all_small ? 'small' : 'large'), i++);
                $openid_btns.append(box);
            }
            if (providers_small) {
                $openid_btns.append('');
                for (id in providers_small) {
                    var box = self.getBox($form, id, providers_small[id], 'small', i++);
                    $openid_btns.append(box);
                }
            }

            $form.find('.openid_input_area').empty();
            var box_id = self.readCookie();
            if (box_id) {
                self.imgClick($form, box_id, true);
            }
        });
    },

    getBox: function($form, box_id, provider, box_size, index) {
        var self = this;
        var $res = $('<span>');
        $res.attr({
            title: this.image_title.replace('{provider}', provider["name"]),
            "data-openid-box-id": box_id,
            class: 'openid_' + box_size + '_btn'
        });
        if (this.no_sprite) {
            var image_ext = box_size == 'small' ? '.ico.gif' : '.gif';
            $res.attr('style', 'background: #FFF url(' + this.img_path + '../images.' + box_size + '/' + box_id + image_ext + ') no-repeat center center" ');
        } else {
            var x = box_size == 'small' ? -index * 24 : -index * 100;
            var y = box_size == 'small' ? -60 : 0;
            $res.attr('style', 'background: #FFF url(' + this.img_path + 'openid-providers-en.png); background-position: ' + x + 'px ' + y + 'px');
        }
        var self = this;
        $res.on('click', function() {
            self.imgClick($form, box_id, false);
        });
        return $res;
    },

    /**
     * Provider image click
     */
    imgClick : function($form, box_id, onload) {
        var provider = providers[box_id];
        if (!provider) {
            return;
        }
        $form.find('.openid_login_hidden').remove();

        $form.data('openid-provider-url', provider.url);
        this.highlight($form, box_id);
        this.setCookie(box_id);

        // prompt user for input?
        if (provider['label']) {
            this.useInputBox($form, provider);
        } else {
            $form.find('.openid_input_area').empty();
            var $hidden = $('<input type="hidden" class="openid_login_hidden" name="openid_login" />');
            $hidden.attr('value', provider.url);
            $form.append($hidden);
            if (!onload) {
                $form.submit();
            }
        }
    },

    highlight : function($form, box_id) {
        // remove previous highlight
        $form.find('.openid_highlight').removeClass('openid_highlight');
        
        // add new highlight
        $form.find('*[data-openid-box-id = "' + box_id + '"]').addClass('openid_highlight');
    },

    setCookie : function(value) {
        var date = new Date();
        date.setTime(date.getTime() + (this.cookie_expires * 24 * 60 * 60 * 1000));
        var expires = "; expires=" + date.toGMTString();
        document.cookie = this.cookie_name + "=" + value + expires + "; path=" + this.cookie_path;
    },

    readCookie : function() {
        var nameEQ = this.cookie_name + "=";
        var ca = document.cookie.split(';');
        for ( var i = 0; i < ca.length; i++) {
            var c = ca[i];
            while (c.charAt(0) == ' ')
                c = c.substring(1, c.length);
            if (c.indexOf(nameEQ) == 0)
                return c.substring(nameEQ.length, c.length);
        }
        return null;
    },

    useInputBox : function($form, provider) {
        var $input_area = $form.find('.openid_input_area');
        $input_area.empty();

        var label = provider['label'];
        if (label) {
            var $p = $('<p>');
            $p.text(label);
            $input_area.append($p);
        }
        
        var value = '';
        var style = '';
        if (provider['name'] == 'OpenID') {
            value = 'http://';
            style = 'background: #FFF url(' + this.img_path + 'openid-inputicon.gif) no-repeat scroll 0 50%; padding-left:18px;';
        }
        $input_area.append($('<input type="text" style="' + style + '" name="openid_login" value="' + value + '" />'));
        var $wrap = $('<div class="input_wrapper submit" />');
        var $submit = $('<input type="submit" />');
        $submit.attr('value', $form.attr('data-i18n-signin-text'));
        $submit.appendTo($wrap);
        $input_area.append($wrap);
    },

    setDemoMode : function(demoMode) {
        this.demo = demoMode;
    }
};
})(jQuery);
