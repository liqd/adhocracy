import re
import cgi

from BeautifulSoup import BeautifulSoup, NavigableString

import adhocracy.model as model
import markdown2 as markdown

from diff import textDiff as html_diff
from tag import tag_normalize, tag_split, tag_cloud_normalize

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

def render(text, substitutions=True):
    if text:
        text = cgi.escape(text)
        text = markdowner.convert(text)
        if substitutions:
            text = SUB_USER.sub(user_sub, text)
            text = SUB_DGB.sub(dgb_sub, text)
    return text