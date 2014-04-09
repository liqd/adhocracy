# Track clicks on links to other websites.
# We implement this similar to google or facebook: The link is rewritten to
# our site, where it gets redirected (by the redirect controller)

import base64
import re
import lxml.etree

from adhocracy import config
from adhocracy.lib.crypto import sign, verify

REDIRECT_SALT = b'static link'


def rewrite_urls(body):
    from adhocracy.lib.helpers import base_url
    if not config.get_bool('adhocracy.track_outgoing_links'):
        return body

    doc = lxml.etree.fromstring('<body>' + body + '</body>')
    for a in doc.xpath('.//a[@href]'):
        if re.match(r'ftps?:|https?:|//', a.attrib['href']):
            url = a.attrib['href']

            # Is it a link to our own site?
            base = base_url('/', instance=None)
            if (url.startswith(base)
                    and not(url.startswith('//') and base == '/')):
                continue

            encoded_url = base64.urlsafe_b64encode(url.encode('utf-8'))
            signed_url = sign(encoded_url, salt=REDIRECT_SALT)
            redirect_url = u'/outgoing_link/' + signed_url.decode('utf-8')
            a.attrib['href'] = base_url(redirect_url)
    res = lxml.etree.tostring(doc)
    return res[len(b'<body>'):-len(b'</body>')]


def decode_redirect(signed_url):
    encoded_url = verify(signed_url.encode('utf-8'), salt=REDIRECT_SALT)
    url = base64.urlsafe_b64decode(encoded_url).decode('utf-8')
    return url
