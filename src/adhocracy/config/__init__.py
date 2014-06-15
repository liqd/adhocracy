import json
import logging
from paste.deploy.converters import asbool
from paste.deploy.converters import asint
from paste.deploy.converters import aslist
from pylons import config
from pylons.i18n import _

log = logging.getLogger(__name__)


DEFAULTS = {
    'adhocracy.allow_organization': False,
    'adhocracy.allow_password_change': False,
    'adhocracy.allow_registration': True,
    'adhocracy.allow_user_html': True,
    'adhocracy.autoassign_permissions': True,
    'adhocracy.background_processing': True,
    'adhocracy.behind_proxy': False,
    'adhocracy.cache_tiles': True,
    'adhocracy.category.long_description.max_length': 20000,
    'adhocracy.comment_wording': False,
    'adhocracy.create_initial_instance_page': True,
    'adhocracy.customize_footer': False,
    'adhocracy.debug.sql': False,
    'adhocracy.delay_update_queue_seconds': 1,
    'adhocracy.delegateable_mediafiles': False,
    'adhocracy.demo_users': [],
    'adhocracy.domain': '',
    'adhocracy.domains': None,  # deprecated
    'adhocracy.email.from': '',
    'adhocracy.enable_behavior': False,
    'adhocracy.enable_gender': False,
    'adhocracy.enable_votedetail': False,
    'adhocracy.enable_welcome': False,
    'adhocracy.export_personal_email': False,
    'adhocracy.external_navigation_base': None,
    'adhocracy.feedback_check_instance': True,
    'adhocracy.feedback_instance_key': u'feedback',
    'adhocracy.feedback_use_categories': True,
    'adhocracy.force_no_http_proxy': False,
    'adhocracy.force_randomized_user_names': False,
    'adhocracy.geo.image_layers': [],
    'adhocracy.geo.instance_overwrites': False,
    'adhocracy.geo.use_instancebadge_colors': True,
    'adhocracy.hide_empty_categories_in_facet_list': False,

    # Final adoption voting has been disabled from the UI during the
    # Adhocracy redesign originally done for enquetebeteiligung.de.
    # Much of the functionality is still in the code, but as long as it's not
    # in the UI, it makes sense to also hide it from the settings UI.
    'adhocracy.hide_final_adoption_votings': False,
    'adhocracy.hide_individual_votes': False,
    'adhocracy.hide_instance_list_in_navigation': False,
    'adhocracy.hide_locallogin': False,
    'adhocracy.include_machine_name_in_header': False,
    'adhocracy.instance.allow_logo_as_background': False,
    'adhocracy.instance_domains': {},
    'adhocracy.instance_domains.enabled': True,
    'adhocracy.instance_footers': [],
    'adhocracy.instance_index_as_tiles': False,
    'adhocracy.instance_index_sidebar': True,
    'adhocracy.instance_key_length_max': 20,
    'adhocracy.instance_key_length_min': 4,

    # an arbitrary list of u'events', u'proposals' and u'milestones'
    'adhocracy.instance_overview_contents': [u'proposals',
                                             u'milestones'],

    # an arbitrary list of u'events'
    'adhocracy.instance_overview_sidebar_contents': [u'events'],

    # comma separated list of instance keys (slugs) or 'ALL'
    'adhocracy.instances.autojoin': '',
    'adhocracy.instance.show_settings_after_create': True,
    'adhocracy.instance_stylesheets': [],
    'adhocracy.instance_themes': [],
    'adhocracy.interactive_debugging': False,
    'adhocracy.language': 'en_US',

    # one of 'OLDEST', 'NEWEST', 'ACTIVITY', 'ALPHA'
    'adhocracy.listings.instance.sorting': 'ACTIVITY',
    'adhocracy.listings.instance_proposal.sorting': None,

    # 'default' or 'alternate'
    'adhocracy.login_style': 'default',
    'adhocracy.milestone.allow_show_all_proposals': False,
    'adhocracy.monitor_browser_values': False,
    'adhocracy.monitor_comment_behavior': False,
    'adhocracy.monitor_extended': False,
    'adhocracy.monitor_external_links': False,
    'adhocracy.monitor_page_performance': False,
    'adhocracy.monitor_pager_clicks': False,
    'adhocracy.number_instance_overview_milestones': 3,
    'adhocracy.page.allow_abstracts': False,
    'adhocracy.post_login_instance': None,
    'adhocracy.post_login_url': None,
    'adhocracy.post_register_instance': None,
    'adhocracy.post_register_url': None,
    'adhocracy.proposal_pager_inline': False,
    'adhocracy.proposal.split_badge_edit': True,
    'adhocracy.propose_optional_attributes': False,
    'adhocracy.protocol': u'http',
    'adhocracy.put_watchlist_in_user_menu': False,
    'adhocracy.readonly': False,
    'adhocracy.readonly.global_admin_exception': True,
    'adhocracy.readonly.message': u'__default__',
    'adhocracy.redirect_startpage_to_instance': u'',
    'adhocracy.registration.email.blacklist': '',
    'adhocracy.registration.require_terms_check': False,
    'adhocracy.registration_support_email': None,
    'adhocracy.relative_urls': False,
    'adhocracy.requestlog_active': False,
    'adhocracy.require_email': True,
    'adhocracy.self_deletion_allowed': True,
    'adhocracy_service.rest_api_address': '',
    'adhocracy_service.rest_api_token': '',
    'adhocracy_service.staticpages.rest_api_address': '',
    'adhocracy_service.verify_ssl': True,
    'adhocracy.session.implementation': 'beaker',
    'adhocracy.set_display_name_on_register': False,
    'adhocracy.setup.drop': "OH_NOES",
    'adhocracy.show_abuse_button': True,
    'adhocracy.show_instance_creators': False,
    'adhocracy.show_instance_fallback_icons': False,
    'adhocracy.show_instance_overview_proposals_all': False,
    'adhocracy.show_instance_overview_stats': True,
    'adhocracy.show_social_buttons': True,
    'adhocracy.show_stats_on_frontpage': True,
    'adhocracy.show_tutorials': True,
    'adhocracy.site.name': 'Adhocracy',
    'adhocracy.startpage.instances.list_length': 0,
    'adhocracy.startpage.proposals.list_length': 0,
    'adhocracy.static.age': 7200,
    'adhocracy.static_agree_text': None,
    'adhocracy.static.category_index_heading': None,

    # On of 'filesystem', 'database', 'external'
    'adhocracy.staticpage_backend': 'filesystem',
    'adhocracy.static.page_index_heading': None,
    'adhocracy.store_notification_events': True,
    'adhocracy.tagcloud_facet': False,
    'adhocracy.themed': False,
    'adhocracy.timezone': 'Europe/Berlin',
    'adhocracy.track_outgoing_links': False,
    'adhocracy.translations': 'adhocracy',
    'adhocracy.use_avatars': True,
    'adhocracy.use_external_navigation': False,
    'adhocracy.use_feedback_instance': False,
    'adhocracy.user.bio.max_length': 1000,
    'adhocracy.user.bio.no_max_length': False,
    'adhocracy.user.display_name.allow_change': True,
    'adhocracy.user.optional_attributes': [],
    'adhocracy.use_test_instance': True,
    'adhocracy.wording.intro_for_overview': False,
    'allow_system_email_in_mass_messages': True,
    # 'beaker.session.secret':
    'debug': False,
    'run_integrationtests': False,
    # 'skip_authentication':
    'smtp_server': 'localhost',
    'smtp_port': 25,
    'sqlalchemy.url': 'sqlite:///production.db',
    # 'memcached.server':

    'adhocracy.redis.host': '127.0.0.1',
    'adhocracy.redis.port': 5006,
    'adhocracy.redis.queue': 'adhocracy.queue',

    'adhocracy.shibboleth.display_name.force_update': False,
    'adhocracy.shibboleth.display_name.function': None,
    'adhocracy.shibboleth.locale.attribute': None,
    'adhocracy.shibboleth_logout_url': None,
    'adhocracy.shibboleth.register_form': True,

    # Configures how to map shibboleth attributes to badges.
    # See lib.auth.shibboleth.
    'adhocracy.shibboleth.userbadge_mapping': [],

    'velruse.domain': 'localhost',
    'velruse.port': 5028,
    'velruse.protocol': 'http',

    # 'adhocracy.twitter.consumer_key':
    # 'adhocracy.twitter.key':
    # 'adhocracy.twitter.profile_url':
    # 'adhocracy.twitter.secret':
    # 'adhocracy.twitter.username':

    # One of None, 'captchasdotnet' and 'recaptcha'.
    'adhocracy.captcha_type': None,

    'captchasdotnet.user_name': None,
    'captchasdotnet.secret': None,
    'captchasdotnet.alphabet': 'abcdefghkmnopqrstuvwxyz',
    'captchasdotnet.letters': 6,
    'captchasdotnet.random_repository': '/tmp/captchasnet-random-strings',
    'captchasdotnet.cleanup_time': 3600,
    'recaptcha.private_key': None,
    'recaptcha.public_key': None,

    # 'piwik.id':
    # 'piwik.site':
}


def get_value(key, converter, default=None, config=config,
              converter_kwargs={}):

    value = config.get(key)

    if value is None:
        if default is not None:
            return default
        else:
            return DEFAULTS.get(key)

    if converter is None:
        return value
    else:
        return converter(value, **converter_kwargs)


def get(key, default=None, config=config):
    """ Return a config value as unicode. """
    return get_value(key, lambda x: x.decode('utf-8'), default, config)


def get_string(key, default=None, config=config):
    """ Return a config value as string.

    This is pretty much the same as pylons.config.get.

    """
    return get_value(key, None, default, config)


def get_bool(key, default=None, config=config):
    return get_value(key, asbool, default, config)


def get_int(key, default=None, config=config):
    return get_value(key, asint, default, config)


def get_list(key, default=None, config=config, sep=',', cast=None):
    result = get_value(key, aslist, default, config, {'sep': sep})
    if cast is None or result is None:
        return result
    else:
        return map(cast, result)


def get_tuples(key, default=[], sep=u' '):
    mapping = get(key, None)
    if mapping is None:
        return default
    return ((v.strip() for v in line.split(sep))
            for line in mapping.strip().split(u'\n')
            if line is not u'')


def get_json(key, default=None, config=config):
    try:
        return get_value(key, json.loads, default, config)
    except ValueError, e:
        log.error("invalid json: %s \nin config option %s" %
                  (config.get(key), key))
        raise


def get_optional_user_attributes():

    TYPES = {
        'unicode': (unicode, lambda v: v.decode('utf-8')),
        'int': (int, int),
        'bool': (bool, asbool),
    }

    def transform(key, type_string, label):
        allowed = get_list('adhocracy.user.optional_attributes.%s' % key, None,
                           sep=';')
        type_, converter = TYPES[type_string]
        if allowed is not None:
            allowed = [{
                'value': converter(v),
                'selected': False,
                'label': converter(v),
            } for v in allowed]

            allowed.insert(0, {
                'value': '',
                'selected': True,
                'label': _(u'Not specified')
            })
        return (key, type_, converter, label, allowed)

    return map(lambda t: transform(*t),
               get_tuples('adhocracy.user.optional_attributes', sep=u','))
