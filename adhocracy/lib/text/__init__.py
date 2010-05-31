import re
import cgi

from BeautifulSoup import BeautifulSoup, NavigableString
import markdown2 as markdown

import adhocracy.model as model
from diff import textDiff as html_diff
from tag import tag_normalize, tag_split, tag_cloud_normalize, tag_split_last
from normalize import *


DEFAULT_TAGS = ['a', 'b', 'strong', 'h1', 'h2',
                'h3', 'h4', 'h5', 'h6', 'i', 
                'table', 'tr', 'th', 'td', 'abbr', 
                'code', 'blockquote', 'em', 'hr',
                'ul', 'ol', 'li', 'p', 'pre', 
                'strike', 'u', 'img', 'cite', 'br']

DEFAULT_ATTRS = ['href', 'width', 'align', 'src', 
                 'alt', 'title']

META_RE = re.compile("(\n|\t|\")", re.MULTILINE)

markdowner = markdown.Markdown() 

def meta_escape(text, markdown=True):
    if markdown:
        text = plain(text)
    text = META_RE.sub(" ", text)
    text = text.strip()
    return text

def plain(html):
    soup = BeautifulSoup(render(html, substitutions=False))
    return u"".join(map(unicode, soup.findChildren(text=True)))

def cleanup(text):
    return text
    
def field_rows(text):
    if text is None:
        return 10
    rows = int((len([ch for ch in text if ch == "\n"]) + len(text)/70))
    return max(min(30, rows), 5)

SUB_USER = re.compile("@([a-zA-Z0-9_\-]{3,255})")

def user_sub(match):
    from adhocracy.lib import helpers as h
    user = model.User.find(match.group(1))
    if user is not None:
        return h.user_link(user)
    return match.group(0)

SUB_DGB = re.compile("#([0-9]*)")

def dgb_sub(match):
    from adhocracy.lib import helpers as h
    dgb = model.Delegateable.find(match.group(1), include_deleted=True)
    if dgb is not None:
        return h.delegateable_link(dgb)
    return match.group(0)

SUB_PAGE = re.compile("\[\[([^(\]\])]{3,255})\]\]", re.M)

def page_sub(match):
    from adhocracy.lib import helpers as h
    page = model.Page.find_fuzzy(match.group(1), include_deleted=True) 
    if page is not None:
        if page.is_deleted():
            return match.group(1)
        return h.page_link(page, icon=not (page.function == page.DOCUMENT))
    else:
        from adhocracy.forms import FORBIDDEN_NAMES
        return h.page_link(match.group(1), create=True)


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
            text = SUB_DGB.sub(dgb_sub, text)
            text = SUB_PAGE.sub(page_sub, text)
            text = SUB_TRANSCLUDE.sub(transclude_sub(transclude_path), text)
    return text