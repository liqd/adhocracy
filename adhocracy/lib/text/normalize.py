

def title2alias(title):
    title = urllib.unquote(title)
    if not isinstance(title, unicode):
        title = unicode(title)
    title = unicodedata.normalize('NFKC', title)
    title = title.strip()
    return title