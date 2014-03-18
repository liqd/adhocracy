Facebook SSO
============


The Facebook single sign on (SSO) is an additional way
of authentification and authorization for adhocracy.

We use `velruse <http://velruse.readthedocs.org>`_ to implement this.


Setting up a Facebook app
-------------------------

To use Facebook SSO you need to create a Facebook app.

Only registered Facebook users, who added a cellphone number to Facebook, can create Facebook apps.

Once you have a Facebook user you can create an app `here <https://developers.facebook.com/apps‎>`_.

Facebook will walk you through email and cellphone authentification, if not done already.
You can use one cellphone number for multiple Facebook accounts!

You need to add the URL of your Adhocracy Installation to your Facebook app.
First go to the Settings tab of your Facebook app, click `Add Platform` and choose `Website`.
Then you enter the URL of your Adhocracy Installation into the Site URL field.
Then you add the same URL to the `App Domains` field of your Facebook apps' Settings.

This will allow your users to login through Facebook from your domain and all its subdomains.

Then go to the `Advanced Tab` your apps' `Settings`.
There you need to enable `Client OAuth Login`.

Enabling Facebook SSO in Adhocracy
----------------------------------

You can find an app secret and an app id in your Facebook app page.
You need to add these to the `buildout.cfg` of your adhocracy installation.

example::

    [velruse]
    facebook_app_key     = 3428935723984
    facebook_app_secret  = 3598b78dsf7s8f9g087230837sd323

Then you need to enable Facebook SSO by adding
facebook to `adhocracy.login_type` in `adhocracy.ini`

example::

    adhocracy.login_type = facebook,openid,username+password,email+password
