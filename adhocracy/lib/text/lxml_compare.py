from lxml import etree
from lxml.html.diff import htmldiff
from lxml.html import fragment_fromstring


def compare_html(left, right):
    return htmldiff(left, right)
    
def compare_html_sections(left, right):
    diffed_html = htmldiff(left, right)
    root = fragment_fromstring(diffed_html, create_parent=True)
    return [etree.tostring(c) for c in root.getchildren()]