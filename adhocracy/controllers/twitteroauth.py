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
    @ActionProtector(has_permission("user.edit"))
    def init(self):
        api = create_oauth()
        
        request_token = api.getRequestToken()
        session['request_token'] = request_token.to_string()
        session.save()
        redirect_to(api.getAuthorizationURL(request_token))
    
    @ActionProtector(has_permission("user.edit"))
    def callback(self):
        request_token = session.get('request_token')
        if not request_token:
            h.flash(_("You have been logged out while authenticating "
                      "at twitter. Please try again."))
            redirect_to("/user/edit/%s" % str(c.user.user_name))
        
        request_token = oauth.OAuthToken.from_string(request_token)
        req_api = create_oauth(key=request_token.key, secret=request_token.secret)
        access_token = req_api.getAccessToken()
        
        api = create_oauth(key=access_token.key, secret=access_token.secret)
        user_data = api.GetUserInfo()
        
        log.debug(access_token)
        log.debug(user_data)
        
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
            h.flash(_("You're now following <b>%s</b> on twitter so Adhocracy " 
                      + "can send you notifications as direct messages") % system_user())
        except HTTPError, he:
            log.warn(he.read())
        
        redirect_to("/user/edit/%s" % str(c.user.user_name))
    
    @RequireInternalRequest()
    @ActionProtector(has_permission("user.edit"))
    def revoke(self):
        if not c.user.twitter:
            h.flash(_("You have no twitter association."))
            redirect_to("/user/edit/%s" % str(c.user.user_name))
        twitter = c.user.twitter
        twitter.delete_time = datetime.now()
        model.meta.Session.add(twitter)
        model.meta.Session.commit()
        redirect_to("/user/edit/%s" % str(c.user.user_name))
