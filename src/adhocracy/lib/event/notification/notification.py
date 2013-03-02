import os.path
import logging

from pylons.i18n import _

from adhocracy import i18n, templates
from adhocracy.lib.templating import render
from adhocracy.lib.event import formatting

log = logging.getLogger(__name__)


class Notification(object):

    TPL_NAME = os.path.join("", "notifications", "%s.%s.txt")

    def __init__(self, event, user, type=None, watch=None):
        self.event = event
        self._type = type
        self.user = user
        self.watch = watch

    def get_type(self):
        if not self._type:
            self._type = self.event.event
        return self._type

    type = property(get_type)

    def get_priority(self):
        return self.type.priority

    priority = property(get_priority)

    def get_id(self):
        return "n-e%s-u%s" % (self.event.id, self.user.id)

    id = property(get_id)

    def language_context(self):
        return i18n.user_language(self.user)

    def get_subject(self):
        fe = formatting.FormattedEvent(self.event,
                                       lambda f, value: f.unicode(value))
        return self.type.subject() % fe

    subject = property(get_subject)

    def _get_link(self):
        try:
            return self.type.link_path(self.event)
        except:
            return ""

    link = property(_get_link)

    def get_body(self):
        locale = self.language_context()
        data = {'n': self, 'e': self.event, 'u': self.user, 't': self.type}

        tpl_name = self.TPL_NAME % (str(self.type), locale.language[0:2])
        tpl_path = os.path.join(templates.__path__[0], tpl_name)

        if not os.path.exists(tpl_path):
            log.warn("Notification body needs to be localized to "
                     "file %s" % (tpl_path))
            tpl_name = self.TPL_NAME % (
                str(self.type), i18n.get_default_locale().language[0:2])

        body = render(tpl_name, data).strip()
        body += _("\r\n\r\nMore info: %(url)s") % dict(url=self.link)
        return body

    body = property(get_body)

    def __repr__(self):
        return "<Notification(%s,%s,%s)>" % (self.type, self.user.user_name,
                                             self.priority)
