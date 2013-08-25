import imaplib2
import email
from email.parser import HeaderParser
import os
import logging
import threading
import time
from pylons import config
from adhocracy.lib.emailcomments import util
from adhocracy.lib import queue

# cfg
IMAP_DOMAIN = config.get('imap_domain')
IMAP_USERNAME = config.get('imap_account')
IMAP_PASSWORD = config.get('imap_password')
COMMENTS_DIR = config.get('imap_directory')
IMAP_PORT = config.get('imap_port')
MAX_INTERVAL = 60 * 64  # max. reconnect-interval (seconds - 60 * 2^n possible)

log = logging.getLogger(__name__)


class Idler(threading.Thread):

    def __init__(self, ecq):
        threading.Thread.__init__(self)
        self.ecq = ecq

    def run(self):
        '''(re)connects to IMAP and waits for new mail'''
        recon_interval = 30
        while True:
            try:
                self.conn = imaplib2.IMAP4_SSL(IMAP_DOMAIN, IMAP_PORT)
                self.conn.login(IMAP_USERNAME, IMAP_PASSWORD)
                self.conn.select(COMMENTS_DIR)
            except Exception as e:
                log.info("IMAP-connection could not be established because:")
                log.info(e)
                if recon_interval < MAX_INTERVAL:
                    recon_interval = recon_interval * 2
                minutes = recon_interval / 60
                log.info("reconnect in {0} minute(s)".format(minutes))
                time.sleep(recon_interval)
                continue

            recon_interval = 30
            log.info("IMAP-connection established")

            while True:
                try:
                    self.dosync()
                    self.conn.idle()
                except self.conn.abort:
                    log.info("IMAP-connection lost, reconnecting...")
                    break

    def dosync(self):
        '''executed if a new mail arrives'''
        typ, data = self.conn.search(None, 'UNSEEN')
        if data[0]:
            for num in data[0].split():
                typ, data = self.conn.fetch(num, '(RFC822)')
                header_data = data[0][1]
                parser = HeaderParser()
                message = parser.parsestr(header_data)
                log.info("new IMAP mail")
                self.ecq.put(message)
