
FEED = ['rss', 'feed', 'atom'] 
HTML = ['html', 'htm', 'xhtml']
JSON = ['json', 'js']
XML = ['xml']

TYPES = {
#    'rss': 'application/xml+rss',
#    HTML: 'text/html',
#    JSON: 'text/javascript',
#    XML:  'application/xml'
    }

def parse_format(format, allow=TYPES.keys()):
    format = unicode(format).strip().lower()
    for _type in allow:
        if format in _type: 
            return _type[0]
    raise ValueError(_("The requested format is not available"))   