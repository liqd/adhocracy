from fanstatic import Library, Group, Resource
# external libraries
from js.jquery import jquery
from js.jquery_joyride import joyride
from js.socialshareprivacy import socialshareprivacy
from adhocracy.i18n import LOCALES


# --[ twitter bootstrap ]---------------------------------------------------

bootstrap_library = Library('bootstrap', 'bootstrap', version="2.1.1")
bootstrap_js = Resource(bootstrap_library, 'js/bootstrap.js',
                        minified='js/bootstrap.min.js',
                        depends=[jquery])
bootstrap = Group([bootstrap_js])


# --[ stylesheets ]---------------------------------------------------------

stylesheets_library = Library('stylesheets', 'stylesheets')
style = Resource(stylesheets_library, 'adhocracy.css')
stylesheets = Group([style])


# --[ jquery.autocomplete ]-------------------------------------------------

autocomplete_library = Library('autocomplete', 'javascripts', version="1.2.2")
autocomplete_js = Resource(autocomplete_library, 'jquery.autocomplete.min.js',
                           depends=[jquery])
autocomplete_css = Resource(autocomplete_library, 'jquery.autocomplete.css')
autocomplete = Group([autocomplete_js, autocomplete_css])


# --[ jquery.i18n ]---------------------------------------------------------

jquery_i18n_library = Library('jquery_i18n', 'javascripts', version='0.9.2')

jquery_i18n_js = Resource(jquery_i18n_library, 'jquery.i18n.js',
                          minified='jquery.i18n.min.js',
                          depends=[jquery])


# --[ other versioned libraries ]-------------------------------------------

placeholder_library = Library('placeholder', 'javascripts', version="2.0.7")
placeholder = Resource(placeholder_library, 'jquery.placeholder.js',
                       minified='jquery.placeholder.min.js',
                       depends=[jquery])

jquerytools_library = Library('jquerytools', 'javascripts', version="1.2.7")
jquerytools = Resource(jquerytools_library, 'jquery.tools.min.js',
                       depends=[jquery])


# --[ misc javascripts ]----------------------------------------------------

misc_library = Library('misc', 'javascripts')
elastic = Resource(misc_library, 'jquery.elastic.js',
                   depends=[jquery])
cycle = Resource(misc_library, 'jquery.multipleelements.cycle.min.js',
                 depends=[jquery])
modernizr = Resource(misc_library, 'modernizr.js',
                     depends=[jquery])
spectrum_css = Resource(misc_library, 'spectrum/spectrum.css')
spectrum = Resource(misc_library, 'spectrum/spectrum.js',
                    minified='spectrum/spectrum.min.js',
                    depends=[jquery, spectrum_css])
select_hierarchy = Resource(misc_library, 'jquery.select-hierarchy.js',
                            minified='jquery.select-hierarchy.min.js',
                            depends=[jquery])


# --[ adhocracy ]-----------------------------------------------------------

adhocracy_library = Library('adhocracy', 'javascripts')
adhocracy = Resource(adhocracy_library, 'adhocracy.js',
                     depends=[jquery, bootstrap_js, elastic,
                              placeholder, modernizr, jquerytools])


# --[ knockout ]------------------------------------------------------------

knockout_library = Library('knockoutjs', 'javascripts')
knockout_js = Resource(knockout_library, 'knockout.debug.js',
                       minified='knockout.js',
                       depends=[jquery])
knockout_mapping_js = Resource(knockout_library, 'knockout.mapping.debug.js',
                               minified='knockout.mapping.js',
                               depends=[knockout_js])
knockout = Group([knockout_js, knockout_mapping_js])
adhocracy_ko = Resource(adhocracy_library, 'adhocracy.ko.js',
                        depends=[adhocracy, knockout])


# --[ openlayers ]----------------------------------------------------------

openlayers_library = Library('openlayers', 'openlayers', version='2.12.2')
openlayers_js = Resource(openlayers_library, 'openlayers.js',
                         minified='openlayers.min.js',
                         depends=[jquery],
                         bottom=True)
openlayers_css = Resource(openlayers_library, 'theme/default/style.css')

openlayers = Group([openlayers_js, openlayers_css])


# --[ openlayers editor ]---------------------------------------------------

ole_library = Library('openlayers-editor', 'openlayers-editor',
                      version='1.0-beta3')
ole_lang_js = Resource(ole_library, 'lib/Editor/Lang/en.js',
                         depends=[openlayers_js])
ole_loader_js = Resource(ole_library, 'lib/loader.js',
                         depends=[openlayers_js])
ole_js = Resource(ole_library, 'ole.min.js',
                  depends=[openlayers_js],
                  bottom=True)
ole_css = Resource(ole_library, 'theme/geosilk/geosilk.css')
ole = Group([ole_js, ole_css])


# --[ misc geo branch only ]------------------------------------------------

jquery_ui_library = Library('jqueryui', 'jqueryui', version='1.8.21.1')

jquery_ui_js = Resource(jquery_ui_library, 'jquery-ui.custom.min.js',
                        depends=[jquery])
jquery_ui_css = Resource(jquery_ui_library, 'jquery-ui.custom.css')
jquery_ui = Group([jquery_ui_js, jquery_ui_css])

adhocracy_geo_js = Resource(adhocracy_library, 'adhocracy.geo.js',
                            depends=[adhocracy, knockout_js, openlayers_js],
                            bottom=True)


# the adhocracy_geo_i18n resources are needed with need_adhocracy_geo_i18n,
# which automatically choses the right locale
adhocracy_geo_i18n = {}
for locale in LOCALES:
    adhocracy_geo_i18n[locale.language] = Resource(
        adhocracy_library, 'adhocracy.geo.i18n-%s.js' % locale.language,
        depends=[jquery_i18n_js], bottom=True)
