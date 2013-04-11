from fanstatic import Library
from fanstatic import Resource
from kotti.fanstatic import NeededGroup
from kotti.fanstatic import edit_needed_js
from kotti.fanstatic import view_needed_js

library = Library('adhocracy_kotti_theme', 'static')
css = Resource(library, 'css/bootstrap.css', minified='css/bootstrap.min.css')

edit_needed = NeededGroup([css, edit_needed_js, ])
view_needed = NeededGroup([css, view_needed_js, ])


def kotti_configure(settings):

    settings['kotti.asset_overrides'] = 'adhocracy_kotti_theme:kotti-overrides/'

    settings['kotti.fanstatic.view_needed'] = 'adhocracy_kotti_theme.view_needed'
    settings['kotti.fanstatic.edit_needed'] = 'adhocracy_kotti_theme.edit_needed'
