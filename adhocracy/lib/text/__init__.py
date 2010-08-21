import re
import cgi
import logging

from BeautifulSoup import BeautifulSoup, NavigableString

from lxml.html import fragment_fromstring

from lxml_compare import compare_html as html_diff
from lxml_compare import compare_html_sections
from tag import tag_normalize, tag_split, tag_cloud_normalize, tag_split_last
from normalize import *
from render import render, render_line_based


META_RE = re.compile("(\n|\t|\")", re.MULTILINE)


log = logging.getLogger(__name__)

def meta_escape(text, markdown=True):
    if markdown:
        text = plain(text)
    text = META_RE.sub(" ", text)
    text = text.strip()
    return text


def plain(html):
    try:
        return fragment_fromstring(html, create_parent=True).text_content()
    except Exception, e:
        log.exception(e)
        return html


def field_rows(text):
    if text is None:
        return 10
    rows = int((len([ch for ch in text if ch == "\n"]) + len(text)/70))
    return max(min(30, rows), 5)

