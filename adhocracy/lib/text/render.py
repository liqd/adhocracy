import re
import cgi

import markdown2 as markdown

import adhocracy.model as model

markdowner = markdown.Markdown() 

SUB_USER = re.compile("@([a-zA-Z0-9_\-]{3,255})")

def user_sub(match):
    from adhocracy.lib import helpers as h
    user = model.User.find(match.group(1))
    if user is not None:
        return h.user.link(user)
    return match.group(0)
    

SUB_PAGE = re.compile("\[\[([^(\]\])]{3,255})\]\]", re.M)

def page_sub(match):
    from adhocracy.lib import helpers as h
    page_name = match.group(1)
    variant = model.Text.HEAD
    if '/' in page_name:
        page_name, variant = page_name.split('/', 1)
    page = model.Page.find_fuzzy(page_name, include_deleted=True) 
    if page is not None:
        if page.is_deleted():
            return page_name
        return h.page.link(page, variant=variant, icon=not (page.function == page.DOCUMENT))
    else:
        from adhocracy.forms import FORBIDDEN_NAMES
        return h.page.redlink(page_name)


SUB_TRANSCLUDE = re.compile("@@([^(@@)]{3,255})@@", re.M)

def transclude_sub(transclude_path):
    if transclude_path is None:
        transclude_path = []
    
    def render_transclusion(match):
        from adhocracy.lib import helpers as h
        page_name, variant = match.group(1), model.Text.HEAD
        if '/' in page_name:
            page_name, variant = page_name.split('/', 1)
        page = model.Page.find_fuzzy(page_name) 
        if variant not in page.variants:
            variant = model.Text.HEAD
        if (page is not None) and (page.id not in transclude_path):
            transclude_path.append(page.id)
            text = page.variant_head(variant).text
            return render(text, transclude_path=transclude_path)
        return match.group(0)
    
    return render_transclusion


def render(text, substitutions=True, transclude_path=None):
    if text is not None:
        text = cgi.escape(text)
        text = markdowner.convert(text)
        if substitutions:
            text = SUB_USER.sub(user_sub, text)
            text = SUB_PAGE.sub(page_sub, text)
            #text = SUB_TRANSCLUDE.sub(transclude_sub(transclude_path), text)
    return text
