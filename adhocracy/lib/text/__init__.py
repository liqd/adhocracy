import re
import cgi

from BeautifulSoup import BeautifulSoup, NavigableString

import adhocracy.model as model
import markdown2 as markdown

from diff import textDiff as html_diff

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
    soup = BeautifulSoup(render(html))
    return u"".join(map(unicode, soup.findChildren(text=True)))

def cleanup(text):
    return text

def render(text):
    if text:
        text = cgi.escape(text)
        text = markdowner.convert(text)
    return text