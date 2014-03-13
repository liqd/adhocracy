import unicodedata
import re
import math

SPLIT_CHARS = " ,;\""
SPLITTER = re.compile(r'[,;\s]*', re.U)


def tag_normalize(text):
    from adhocracy.lib import helpers as h
    text = h.url.unquote(text)
    text = unicodedata.normalize('NFKC', text)
    return text.strip(SPLIT_CHARS).lower()


def tag_split(text):
    tags = []
    for tag in SPLITTER.split(text):
        if (tag in tags) or (not len(tag)):
            continue
        try:
            int(tag)
        except ValueError:
            tags.append(tag)
    return tags


def tag_split_last(text):
    tags = tag_split(text)
    if not len(tags):
        return (text, '')
    last = tags[-1]
    if not len(last):
        return (text, '')
    return (text[:len(text) - len(last)], last)
