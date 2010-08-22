import re
import cgi
import logging

from BeautifulSoup import BeautifulSoup, NavigableString

from lxml.html import fragment_fromstring

import diff
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


def text_rows(text):
    rows = len(list(text.lines))
    return max(min(30, rows), 10)

def revision_rows(revision):
    if revision.text is None:
        return 5
    rows = int((len([ch for ch in revision.text if ch == "\n"]) + len(revision.text)/70))
    return max(min(30, rows), 5)

