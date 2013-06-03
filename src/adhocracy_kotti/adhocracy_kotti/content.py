import colander
from kotti.resources import Document
from kotti.util import _
from kotti.views.edit.content import DocumentSchema
from kotti.views.edit.content import DocumentEditForm
from kotti.views.edit.content import DocumentAddForm
from pyramid.threadlocal import get_current_request


def validate_slug(node, value):

    request = get_current_request()
    if value in request.context:
        raise colander.Invalid(
            node, _("This slug is already used in the current context"))


class SlugDocumentSchema(DocumentSchema):
    name = colander.SchemaNode(
        colander.String(),
        title=_(u'Slug (URL-Snippet)'),
        insert_before=u'title',
        validator=validate_slug,
    )


class SlugDocumentEditForm(DocumentEditForm):
    schema_factory = SlugDocumentSchema


class SlugDocumentAddForm(DocumentAddForm):
    schema_factory = SlugDocumentSchema
    add = Document
    item_type = _(u"Document")
