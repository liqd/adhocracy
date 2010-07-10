from lxml import etree
from lxml.html.diff import htmldiff


def compare_html(left, right):
    return htmldiff(left, right)
    