import pyinotify
import logging
import os
import time
from datetime import datetime
import mailbox
import email
import shutil
from adhocracy.lib.emailcomments import util

log = logging.getLogger(__name__)


def maildir(path, ecq):
    '''gets payload and recipient of a new Maildir mail'''
    time.sleep(1)  # pause - else mail isn't yet in tmp
    log.info("new mail in Maildir")

    for filename in os.listdir(os.path.join(path, "new")):
        file_path = os.path.join(path, "new", filename)
        mail = open(file_path, "r")
        parser = email.Parser.Parser()
        message = parser.parse(mail)
        mail.close()
        ecq.put(message)
        util.move_overwrite(file_path,
                os.path.join(path, "cur", filename))


def mbox(path, ecq):
    '''gets payload and recipient of a new mbox mail'''
    time.sleep(1)  # pause - MTA could do something yet
    log.info("new mail in mbox")

    tmp_mb = os.path.join("/var/tmp", str(datetime.now()))
    shutil.copy(path, tmp_mb)

    mbox = mailbox.mbox(tmp_mb)

    # process latest email
    try:
        message = mbox.get_message(mbox.keys()[-1])
    except Exception as e:
        log.error("mbox empty, or header malformed:")
        log.error(e)
        os.remove(tmp_mb)
        return
    ecq.put(message)
    os.remove(tmp_mb)


def watch_new_mail(path_md, path_mb, ecq):
    '''
    Uses pyinotify to watch for new local emails.
    If a new email arrives it will handled by the ec-Queue.
    '''
    wm = pyinotify.WatchManager()
    mask_md = pyinotify.IN_CREATE  # watch for new files in maildir
    mask_mb = pyinotify.IN_CLOSE_WRITE  # watch for changed mbox

    class PTmp(pyinotify.ProcessEvent):

        def process_IN_CREATE(self, event):
            maildir(path_md, ecq)

        def process_IN_CLOSE_WRITE(self, event):
            mbox(path_mb, ecq)

    notifier = pyinotify.ThreadedNotifier(wm, PTmp())
    notifier.start()

    wdd = wm.add_watch(path_md, mask_md, rec=True)
    wm.add_watch(path_mb, mask_mb, rec=False)
    wm.rm_watch(wdd[os.path.join(path_md, "cur")], rec=True)
