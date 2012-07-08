from pylons import config, request
from webhelpers.html import literal

from recaptcha.client.captcha import displayhtml
from recaptcha.client.captcha import submit
from recaptcha.client.captcha import RecaptchaResponse


class Recaptcha(object):
    """Recaptcha functionality for Pylons applications.

Add the following items to your config.ini:

::

    recaptcha.public_key = yourpublickey
    recaptcha.private_key = yourprivatekey

Example usage:

::

    #in the controller that renders the recaptcha-proected form::
    c.recaptcha = h.recaptcha.displayhtml() #insert c.recaptcha into the form

    #in the controller that handles the form POST::
    recaptcha_response = h.recaptcha.submit()
    if not recaptcha_response.is_valid:
        #render the form and try again
        c.recaptcha = h.recaptcha.displayhtml(
            error=recaptcha_response.error_code)

"""

    def __init__(self):
        """
        Recaptcha might be called before config is parsed,
        e.g. in project.lib.helpers, so defer config lookup
        """
        RecaptchaResponse

    @property
    def _public_key(self):
        return config.get('recaptcha.public_key')

    @property
    def _private_key(self):
        return config.get('recaptcha.private_key')

    def displayhtml(self, use_ssl=False, error=None):
        """Return HTML string for inserting recaptcha into a form."""
        return literal(displayhtml(self._public_key, use_ssl=use_ssl,
                                   error=error))

    def submit(self):
        """Return an instance of recaptcha.client.captcha.RecaptchaResponse."""
        if request.environ.get('paste.testing', False):
            return RecaptchaResponse(False, 'paste.testing')
        recaptcha_challenge_field = request.POST.get(
            'recaptcha_challenge_field', None)
        recaptcha_response_field = request.POST.get('recaptcha_response_field',
                                                    None)
        return submit(recaptcha_challenge_field, recaptcha_response_field,
                      self._private_key, "127.0.0.1")
