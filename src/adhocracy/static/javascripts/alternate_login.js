$(document).ready(function() {
  $('input[name=login]').focus();

  var password_field = $('.login-alternate input[name="password"]');
  var onChange = function(e) {
    if (password_field.val() || (e && e.keyCode != 9)) {
      $('.login-alternate input[name="have_password"][value="true"]').attr('checked', 'checked');
    }
  };
  password_field.on('change click keypress paste propertychanged', onChange);
  
  // Detect autofill
  onChange();
  window.setTimeout(onChange, 50);
});
