from adhocracy_kotti.content import Document
from adhocracy_kotti.content import SlugDocumentEditForm
from adhocracy_kotti.content import SlugDocumentAddForm


def kotti_configure(settings):

    settings['kotti.image_scales.icon'] = '16x16'  # <max_width>x<max_height>
    settings['kotti.image_scales.thumb'] = '48x48'
    settings['kotti.image_scales.small'] = '128x128'
    settings['kotti.image_scales.logo'] = '300x90'
    settings['kotti.image_scales.middle'] = '632x632'
    settings['kotti.image_scales.large'] = '1004x1004'


def includeme(config):

    config.include("cornice")
    config.scan(__name__)
    config.add_view(
        SlugDocumentEditForm,
        context=Document,
        name='edit',
        permission='edit',
        renderer='kotti:templates/edit/node.pt',
    )

    config.add_view(
        SlugDocumentAddForm,
        name=Document.type_info.add_view,
        permission='add',
        renderer='kotti:templates/edit/node.pt',
    )
