import unicodedata
import re
import math
import urllib

SPLIT_CHARS = " ,;\""
SPLITTER = re.compile(r'[,;\s]*', re.U)


def tag_normalize(text):
    text = urllib.unquote(text)
    if not isinstance(text, unicode):
        text = unicode(text)
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


def tag_cloud_normalize(tags, steps=6):
    if not len(tags):
        return tags
    newThresholds, results = [], []
    temp = [c for (t, c) in tags]
    maxWeight = float(max(temp))
    minWeight = float(min(temp))
    newDelta = (maxWeight - minWeight) / float(steps)
    for i in range(steps + 1):
        newThresholds.append((100 * math.log((minWeight + i * newDelta) + 2),
                              i))
    for (tag, count) in tags:
        fontSet = False
        for threshold in newThresholds[1:int(steps) + 1]:
            if (100 * math.log(count + 2)) <= threshold[0] and not fontSet:
                results.append((tag, count, threshold[1]))
                fontSet = True
    return results
