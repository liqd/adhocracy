import logging
from datetime import datetime

from oauth import oauth
from pylons.i18n import _
from urllib2 import HTTPError

from adhocracy.lib.base import *
from adhocracy.lib.microblog import create_api, create_oauth, system_user

log = logging.getLogger(__name__)

class TwitteroauthController(BaseController):

    @RequireInternalRequest()
    def init(self):
        require.user.edit(c.user)
        api = create_oauth()
        request_token = api.getRequestToken()
        session['request_token'] = request_token.to_string()
        session.save()
        redirect(api.getAuthorizationURL(request_token))
    
    
    def callback(self):
        require.user.edit(c.user)
        if 'denied' in request.params:
            redirect(h.entity_url(c.user, member='edit'))
        request_token = session.get('request_token')
        if not request_token:
            h.flash(_("You have been logged out while authenticating "
                      "at twitter. Please try again."))
            redirect(h.entity_url(c.user, member='edit'))
        request_token = oauth.OAuthToken.from_string(request_token)
        req_api = create_oauth(key=request_token.key, secret=request_token.secret)
        access_token = req_api.getAccessToken()
        api = create_oauth(key=access_token.key, secret=access_token.secret)
        user_data = api.GetUserInfo()
        twitter = model.Twitter(int(user_data.id), c.user, 
                                user_data.screen_name, 
                                unicode(access_token.key), 
                                unicode(access_token.secret))
        model.meta.Session.add(twitter)
        model.meta.Session.commit()
        try:
            # workaround to a hashing fuckup in oatuh
            api._FetchUrl("http://twitter.com/friendships/create.json", 
                          post_data={'screen_name': system_user()}, 
                          no_cache=True)
            h.flash(_("You're now following %s on twitter so we " 
                      + "can send you notifications as direct messages") % system_user())
        except HTTPError, he:
            log.warn(he.read())
        redirect(h.entity_url(c.user, member='edit'))
    
    
    @RequireInternalRequest()
    def revoke(self):
        require.user.edit(c.user)
        if not c.user.twitter:
            h.flash(_("You have no twitter association."))
            redirect(h.entity_url(c.user, member='edit'))
        c.user.twitter.delete()
        model.meta.Session.commit()
        redirect(h.entity_url(c.user, member='edit'))
