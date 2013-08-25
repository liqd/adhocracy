import os
from pylons import config
import getpass
import logging
import Queue
from sqlalchemy.orm import sessionmaker, scoped_session
from adhocracy.model import meta

log = logging.getLogger(__name__)


def mail_watch():
    '''
    This is a script executed by the adhocracy emailcommentworker
    Its target is to listen to new mails (Maildir and mbox or IMAP)
    and identify if they are comment replies. If so the jobs
    will be executed in a queue.
    '''
    esrc = config.get("email_src")

    if esrc == "imap" or esrc == "local":
        ecq = Queue.Queue()

        Session = sessionmaker(bind=meta.engine, autoflush=True)
        meta.Session = scoped_session(Session)

        from adhocracy.lib.emailcomments import parseincoming
        if esrc == "imap":
            from adhocracy.lib.emailcomments import imap
            idler = imap.Idler(ecq)
            idler.start()
        elif esrc == "local":
            from adhocracy.lib.emailcomments import localwatch
            username = config.get("local_user")
            if not username:
                log.error("no user set in config")
                log.info("emailcomments are disabled")
                return
            if username:
                path_md = os.path.join("/home", username, "Maildir")
                path_mb = os.path.join("/var/mail", username)
                if os.path.exists("/usr/include/linux/inotify.h"):
                    if util.create_filesystem(path_md):
                        localwatch.watch_new_mail(path_md, path_mb, ecq)
                    else:
                        return
                else:
                    log.error("kernel module inotify is not installed")
                    log.info("emailcomments are disabled")
                    return
            else:
                log.error("user cannot be determined")
                log.info("emailcomments are disabled")
                return

        while True:
            message = ecq.get()
            parseincoming.handle_inc_mail(message)
