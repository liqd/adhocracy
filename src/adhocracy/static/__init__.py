from fanstatic import Library, Group, Resource
# external libraries
from js.jquery import jquery
from js.jquery_joyride import joyride
from js.socialshareprivacy import socialshareprivacy


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
openid_selector = Resource(misc_library, 'openid.js',
                            depends=[jquery])


# --[ adhocracy ]-----------------------------------------------------------

adhocracy_library = Library('adhocracy', 'javascripts')
adhocracy = Resource(adhocracy_library, 'adhocracy.js',
                     depends=[jquery, bootstrap_js, elastic,
                              placeholder, modernizr, jquerytools,
                              openid_selector])


# --[ knockout ]------------------------------------------------------------

knockout_library = Library('knockoutjs', 'javascripts', version="2.2.1")
knockout_js = Resource(knockout_library, 'knockout.debug.js',
                       minified='knockout.js',
                       depends=[jquery])
knockout_mapping_js = Resource(knockout_library, 'knockout.mapping.debug.js',
                               minified='knockout.mapping.js',
                               depends=[knockout_js])
knockout = Group([knockout_js, knockout_mapping_js])
adhocracy_ko = Resource(knockout_library, 'adhocracy.ko.js',
                        depends=[adhocracy, knockout])
