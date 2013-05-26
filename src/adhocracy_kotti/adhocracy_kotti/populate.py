"""
Setup initial content
"""

from kotti.resources import DBSession
from kotti.resources import Node
from kotti.resources import Document
from kotti.security import SITE_ACL
from kotti.workflow import get_workflow
from kotti.populate import populate_users


def populate():
    """
    Create the root node (:class:`~kotti.resources.Document`) and
    subnodes for every configured language.
    """
    #TODO make it DRY
    #TODO set edit permissions
    if DBSession.query(Node).count() == 0:
        root = Document(**_ROOT_ATTRS)
        root.__acl__ = SITE_ACL
        DBSession.add(root)
        root['de'] = Document(**_DE_ATTRS)
        root['de']['mainmennu'] = Document(**_MAINMENU_ATTRS)
        root['de']['footer'] = Document(**_FOOTER_ATTRS)
        root['en'] = Document(**_EN_ATTRS)
        root['en']['mainmennu'] = Document(**_MAINMENU_ATTRS)
        root['en']['footer'] = Document(**_FOOTER_ATTRS)
        root['mediacenter'] = Document(**_MEDIACENTER_ATTRS)

        wf = get_workflow(root)
        if wf is not None:
            DBSession.flush()  # Initializes workflow
            wf.transition_to_state(root, None, u'public')
            wf.transition_to_state(root["de"], None, u'public')
            wf.transition_to_state(root["de"]['mainmennu'], None, u'public')
            wf.transition_to_state(root["de"]['footer'], None, u'public')
            wf.transition_to_state(root["en"], None, u'public')
            wf.transition_to_state(root["en"]['mainmennu'], None, u'public')
            wf.transition_to_state(root["en"]['footer'], None, u'public')
            wf.transition_to_state(root["mediacenter"], None, u'public')

    populate_users()


_ROOT_ATTRS = dict(
    name=u'',  # (at the time of writing) root must have empty name!
    title=u'Welcome to Kotti',
    description=u'Congratulations! You have successfully installed Kotti.',
    body=u""" """
)


_DE_ATTRS = dict(
    name=u'de',
    title=u'DE translations',
    description=u'Folder for german translations.',
    body=u""" """
)


_EN_ATTRS = dict(
    name=u'en',
    title=u'EN translations',
    description=u'Folder for english translations.',
    body=u""" """
)


_MAINMENU_ATTRS = dict(
    name=u'mainmennu',
    title=u'Mainmenu',
    description=u'Documents to generate the adhocracy main menu.',
    body=u""" """
)

_FOOTER_ATTRS = dict(
    name=u'footer',
    title=u'Footer',
    description=u'Document to replace the adhocracy footer',
    body=u""" """
)


_MEDIACENTER_ATTRS = dict(
    name=u'mediacenter',
    title=u'Mediacenter',
    description=u'Folder to stores media center files (webservice for'
                ' adhocracy). DONT CHANGE files here manually.',
    body=u""" """
)
