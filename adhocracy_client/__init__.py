import adhocracy.lib.helpers
import adhocracy.model
from . import static

need = adhocracy.lib.helpers.FanstaticNeedHelper(static)
# Monkey-patch need for the templates later on
adhocracy.lib.helpers.need = need

import pylons
import pylons.templating

def render(template_name, value, only_fragment):
    if only_fragment:
        return render_def(template_name, value)
    else:
        return render_mako(template_name, value)

def tpl_vars():
    vars = dict()
    import adhocracy.lib
    from adhocracy.lib import auth, sorting, text, tiles
    vars['tiles'] = tiles
    vars['lib'] = adhocracy.lib
    vars['can'] = auth.can
    vars['check'] = auth.check
    vars['diff'] = text.diff
    vars['sorting'] = sorting
    vars['model'] = adhocracy.model
    return vars


def render_mako(template_name, data, extra_vars=None, cache_key=None,
           cache_type=None, cache_expire=None, overlay=False):
    """
    Signature matches that of pylons actual render_mako. Except
    for the *overlay* parameter. If it is *True*, the template will
    be rendered in a minimal template containing only the main content
    markup of the site.
    """
    if not extra_vars:
        extra_vars = {}

    extra_vars.update(tpl_vars())

    if overlay:
        extra_vars['root_template'] = '/overlay.html'

    for k,v in data.items():
        setattr(pylons.tmpl_context, k, v)

    page = pylons.templating.render_mako(template_name, extra_vars=extra_vars,
                       cache_key=cache_key, cache_type=cache_type,
                       cache_expire=cache_expire)
    return page


def render_def(template_name, def_name, extra_vars=None, cache_key=None,
               cache_type=None, cache_expire=None, **kwargs):
    """
    Signature matches that of pylons actual render_mako_def.
    """
    if not extra_vars:
        extra_vars = {}

    extra_vars.update(tpl_vars())
    extra_vars.update(kwargs)

    return pylons.templating.render_mako_def(template_name, def_name,
                           cache_key=cache_key, cache_type=cache_type,
                           cache_expire=cache_expire, **extra_vars)
