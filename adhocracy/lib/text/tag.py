import unicodedata
import re
import math

SPLIT_CHARS = " ,;\""
SPLITTER = re.compile(r'[,;\s]*', re.U)

def tag_normalize(text):
    if not isinstance(text, unicode):
        text = unicode(text)
    text = unicodedata.normalize('NFKC', text)
    return text.strip(SPLIT_CHARS)
    
def tag_split(text):
    tags = SPLITTER.split(text)
    return set(filter(len, tags))
    
    
def tag_cloud_normalize(tags, steps=6):
    newThresholds, results = [], []
    temp = [c for (t, c) in tags]
    maxWeight = float(max(temp))
    minWeight = float(min(temp))
    newDelta = (maxWeight - minWeight)/float(steps)
    for i in range(steps + 1):
       newThresholds.append((100 * math.log((minWeight + i * newDelta) + 2), i))
    for (tag, count) in tags:
        fontSet = False
        for threshold in newThresholds[1:int(steps)+1]:
            if (100 * math.log(count + 2)) <= threshold[0] and not fontSet:
                results.append((tag, threshold[1]))
                fontSet = True
    return results
