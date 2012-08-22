from fanstatic import Library, Group, Resource, init_needed
# external libraries
from js.jquery import jquery
from js.jquery_joyride import joyride
from js.socialshareprivacy import socialshareprivacy
from adhocracy.i18n import LOCALES


# --[ yaml ]----------------------------------------------------------------

yaml_library = Library('yaml', 'yaml', version="3.2.1")
yaml_base = Resource(yaml_library, 'core/base.css')
yaml_print = Resource(yaml_library, 'print/print_draft.css',
                      depends=[yaml_base])
yaml = Group([yaml_base, yaml_print])


# --[ twitter bootstrap ]---------------------------------------------------

bootstrap_library = Library('bootstrap', 'bootstrap', version="2.0.4")
bootstrap_js = Resource(bootstrap_library, 'js/bootstrap.js',
                        minified='js/bootstrap.min.js',
                        depends=[jquery])
bootstrap_css = Resource(bootstrap_library, 'css/bootstrap.css',
                         minified='css/bootstrap.min.css',
                         depends=[yaml])  # include it after yaml
bootstrap = Group([bootstrap_js, bootstrap_css])


# --[ stylesheets ]---------------------------------------------------------

stylesheets_library = Library('stylesheets', 'stylesheets')
fonts = Resource(stylesheets_library, 'screen/fonts.css',
                   depends=[yaml, bootstrap_css])
basemod = Resource(stylesheets_library, 'screen/basemod.css',
                   depends=[fonts])
content = Resource(stylesheets_library, 'screen/content.css',
                   depends=[basemod])
style = Resource(stylesheets_library, 'style.css',
                 depends=[content])
stylesheets = Group([yaml, fonts, basemod, content, style])


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

# --[ misc javascripts ]----------------------------------------------------

misc_library = Library('misc', 'javascripts')
elastic = Resource(misc_library, 'jquery.elastic.js',
                   depends=[jquery])
label_over = Resource(misc_library, 'jquery.label_over.js',
                      depends=[jquery])
cycle = Resource(misc_library, 'jquery.multipleelements.cycle.min.js',
                 depends=[jquery])
modernizr = Resource(misc_library, 'modernizr.js',
                     depends=[jquery])
jquerytools = Resource(misc_library, 'jquery.tools.min.js',
                       depends=[jquery])
spectrum_css = Resource(misc_library, 'spectrum/spectrum.css')
spectrum = Resource(misc_library, 'spectrum/spectrum.js',
                    minified='spectrum/spectrum.min.js',
                       depends=[jquery, spectrum_css])


# --[ knockout ]------------------------------------------------------------

knockout_library = Library('knockoutjs', 'javascripts')
knockout_js = Resource(knockout_library, 'knockout.debug.js',
                       minified='knockout.js',
                       depends=[jquery])
knockout_mapping_js = Resource(knockout_library, 'knockout.mapping.debug.js',
                               minified='knockout.mapping.js',
                               depends=[knockout_js])
knockout = Group([knockout_js, knockout_mapping_js])


# --[ openlayers ]----------------------------------------------------------

openlayers_library = Library('openlayers', 'openlayers', version='2.12.1')
openlayers_js = Resource(openlayers_library, 'openlayers.js',
                         minified='openlayers.min.js',
                         depends=[jquery],
                         bottom=True)
openlayers_css = Resource(openlayers_library, 'theme/default/style.css')

openlayers = Group([openlayers_js, openlayers_css])


# --[ misc geo branch only ]------------------------------------------------

jquery_ui_library = Library('jqueryui', 'jqueryui', version='1.8.21.1')

jquery_ui_js = Resource(jquery_ui_library, 'jquery-ui.custom.min.js',
                        depends=[jquery])
jquery_ui_css = Resource(jquery_ui_library, 'jquery-ui.custom.css')
jquery_ui = Group([jquery_ui_js, jquery_ui_css])


# --[ adhocracy ]-----------------------------------------------------------

adhocracy_library = Library('adhocracy', 'javascripts')
adhocracy = Resource(adhocracy_library, 'adhocracy.js',
                     depends=[jquery, bootstrap_js, elastic,
                              label_over, modernizr, jquerytools])
adhocracy_ko = Resource(adhocracy_library, 'adhocracy.ko.js',
                        depends=[adhocracy, knockout])
adhocracy_geo_js = Resource(adhocracy_library, 'adhocracy.geo.js',
                            depends=[adhocracy, knockout_js, openlayers_js],
                            bottom=True)

adhocracy_geo_css = Resource(stylesheets_library, 'adhocracy.geo.css')


# the adhocracy_geo_i18n resources are needed with need_adhocracy_geo_i18n,
# which automatically choses the right locale
adhocracy_geo_i18n = {}
for locale in LOCALES:
    adhocracy_geo_i18n[locale.language] = Resource(
        adhocracy_library, 'adhocracy.geo.i18n-%s.js' % locale.language,
        depends=[jquery_i18n_js], bottom=True)
